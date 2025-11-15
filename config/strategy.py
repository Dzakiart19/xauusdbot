"""
Strategy Configuration & Risk Management Engine
Multi-timeframe signal generation with risk controls
"""

import os
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from config.settings import (
    EMA_PERIODS_FAST, EMA_PERIODS_MED, EMA_PERIODS_SLOW, EMA_TREND_TIMEFRAME,
    RSI_PERIOD, RSI_TIMEFRAME, RSI_OVERSOLD_LEVEL, RSI_OVERBOUGHT_LEVEL,
    STOCH_K_PERIOD, STOCH_D_PERIOD, STOCH_SMOOTH_K, STOCH_TIMEFRAME,
    STOCH_OVERSOLD_LEVEL, STOCH_OVERBOUGHT_LEVEL,
    ATR_PERIOD, ATR_TIMEFRAME, SL_ATR_MULTIPLIER, DEFAULT_SL_PIPS, SL_BUFFER_FOR_SPREAD,
    TP_RR_RATIO, DEFAULT_TP_PIPS,
    VOLUME_THRESHOLD_MULTIPLIER, VOLUME_LOOKBACK_PERIOD,
    MAX_SPREAD_PIPS, SPREAD_CHECK_DURATION,
    MIN_SIGNAL_CONFIDENCE, SIGNAL_COOLDOWN_SECONDS,
    MAX_TRADES_PER_DAY, DAILY_LOSS_PERCENT, RISK_PER_TRADE_PERCENT,
    MAX_CONCURRENT_TRADES, TRADE_SESSION_FILTER, AVOID_LONDON_OPEN, AVOID_US_MAJOR_NEWS,
    EVALUATION_MODE, VIRTUAL_INITIAL_BALANCE, LOT_SIZE
)
from utils.indicators import IndicatorCalculator
from utils.logger import get_logger
from data.models import Trade, TradeStatus, TradeDirection, BotState
import uuid

logger = get_logger()

class StrategyEngine:
    """
    Multi-timeframe signal generation engine
    Combines EMA trend, RSI momentum, Stochastic confirmation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.calc = IndicatorCalculator()
        self.last_signal_time = {}  # Track cooldown per direction
        self.virtual_balance = VIRTUAL_INITIAL_BALANCE
        self.trades_today = 0
        self.daily_loss = 0.0
    
    def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal based on multi-timeframe analysis
        
        Returns:
            Signal dict if valid, None otherwise
        """
        
        # Get close prices for indicators
        m1_closes = market_data.get("m1_closes", [])
        m5_closes = market_data.get("m5_closes", [])
        m1_highs = market_data.get("m1_highs", [])
        m1_lows = market_data.get("m1_lows", [])
        m5_highs = market_data.get("m5_highs", [])
        m5_lows = market_data.get("m5_lows", [])
        m1_volumes = market_data.get("m1_volumes", [])
        current_price = market_data.get("current_price", 0)
        bid = market_data.get("bid", 0)
        ask = market_data.get("ask", 0)
        timestamp = market_data.get("timestamp", datetime.utcnow())
        
        # Check minimum data requirements
        if len(m1_closes) < max(EMA_PERIODS_SLOW, RSI_PERIOD, STOCH_K_PERIOD, ATR_PERIOD):
            return None
        
        # ===== COMPONENT 1: EMA TREND (40%) =====
        ema_alignment = self.calc.get_ema_alignment(m5_closes, EMA_PERIODS_FAST, EMA_PERIODS_MED, EMA_PERIODS_SLOW)
        ema_score = 40 if ema_alignment != "NEUTRAL" else 0
        
        # ===== COMPONENT 2: RSI MOMENTUM (25%) =====
        rsi_vals = self.calc.calculate_rsi(m1_closes, RSI_PERIOD)
        current_rsi = rsi_vals[-1]
        prev_rsi = rsi_vals[-2] if len(rsi_vals) > 1 else current_rsi
        
        rsi_score = 0
        signal_direction = None
        
        # RSI oversold (buy signal)
        if self.calc.is_rsi_oversold(current_rsi, RSI_OVERSOLD_LEVEL):
            if current_rsi > prev_rsi:  # RSI rising from oversold
                rsi_score = 25
                signal_direction = "BUY"
        
        # RSI overbought (sell signal)
        elif self.calc.is_rsi_overbought(current_rsi, RSI_OVERBOUGHT_LEVEL):
            if current_rsi < prev_rsi:  # RSI falling from overbought
                rsi_score = 25
                signal_direction = "SELL"
        
        # ===== COMPONENT 3: STOCHASTIC CONFIRMATION (25%) =====
        stoch_k, stoch_d = self.calc.calculate_stochastic(m1_highs, m1_lows, m1_closes, STOCH_K_PERIOD, STOCH_SMOOTH_K, STOCH_D_PERIOD)
        current_k = stoch_k[-1]
        current_d = stoch_d[-1]
        
        stoch_score = 0
        stoch_direction = None
        
        # Stochastic buy (K > D, both oversold)
        if self.calc.is_stoch_oversold(current_k, STOCH_OVERSOLD_LEVEL):
            if current_k > current_d:  # K crosses above D
                stoch_score = 25
                stoch_direction = "BUY"
        
        # Stochastic sell (K < D, both overbought)
        elif self.calc.is_stoch_overbought(current_k, STOCH_OVERBOUGHT_LEVEL):
            if current_k < current_d:  # K crosses below D
                stoch_score = 25
                stoch_direction = "SELL"
        
        # ===== COMPONENT 4: VOLATILITY FILTER (5%) =====
        atr_vals = self.calc.calculate_atr(m5_highs, m5_lows, m5_closes, ATR_PERIOD)
        current_atr = atr_vals[-1]
        avg_atr = sum(atr_vals[-10:]) / 10 if len(atr_vals) >= 10 else current_atr
        
        volatility_score = 0
        if current_atr < 2 * avg_atr:  # Market not too choppy
            volatility_score = 5
        
        # ===== COMPONENT 5: VOLUME SPIKE (5%) =====
        vol_avg = self.calc.calculate_volume_sma(m1_volumes, VOLUME_LOOKBACK_PERIOD)
        current_vol = m1_volumes[-1]
        avg_vol = vol_avg[-1] if vol_avg else current_vol
        
        volume_score = 0
        if self.calc.is_volume_spike(current_vol, avg_vol, VOLUME_THRESHOLD_MULTIPLIER):
            volume_score = 5
        
        # ===== CONFIDENCE CALCULATION =====
        # All components must agree on direction
        if ema_alignment == "NEUTRAL" or signal_direction is None:
            return None
        
        if signal_direction != ema_alignment.upper()[:3]:  # BUY or SELL match
            return None
        
        if stoch_direction and stoch_direction != signal_direction:
            return None
        
        total_confidence = ema_score + rsi_score + stoch_score + volatility_score + volume_score
        
        if total_confidence < MIN_SIGNAL_CONFIDENCE:
            return None
        
        # ===== ADDITIONAL VALIDATIONS =====
        if not self._check_cooldown(signal_direction):
            return None
        
        if not self._check_session_filter(timestamp):
            return None
        
        spread = ask - bid
        if spread > MAX_SPREAD_PIPS * 0.01:  # Convert pips to price
            return None
        
        # ===== CALCULATE SL & TP =====
        sl_price, tp_price, rr_ratio = self._calculate_levels(
            signal_direction, current_price, current_atr, spread
        )
        
        # ===== CREATE SIGNAL =====
        signal = {
            "signal_id": str(uuid.uuid4()),
            "direction": signal_direction,
            "entry_price": current_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "rr_ratio": rr_ratio,
            "confidence_score": total_confidence,
            "timestamp": timestamp.isoformat(),
            "ema_alignment": ema_alignment,
            "rsi": current_rsi,
            "stoch_k": current_k,
            "stoch_d": current_d,
            "atr": current_atr,
            "spread": spread,
        }
        
        # Log signal generation
        logger.info(f"Signal Generated: {signal_direction} @ {current_price:.2f}, Conf: {total_confidence}%")
        
        return signal
    
    def _check_cooldown(self, direction: str) -> bool:
        """Check if enough time has passed since last signal in same direction"""
        last_time = self.last_signal_time.get(direction, 0)
        current_time = datetime.utcnow().timestamp()
        
        if current_time - last_time < SIGNAL_COOLDOWN_SECONDS:
            return False
        
        self.last_signal_time[direction] = current_time
        return True
    
    def _check_session_filter(self, timestamp: datetime) -> bool:
        """Check if current time is within trading session"""
        if not TRADE_SESSION_FILTER:
            return True
        
        hour = timestamp.hour
        
        # Avoid London Open (07:00-09:00 GMT / 07:30-08:30 GMT)
        if AVOID_LONDON_OPEN and 7 <= hour <= 9:
            return False
        
        # Avoid US Major News (13:30-15:00 GMT / 14:00-14:30 GMT)
        if AVOID_US_MAJOR_NEWS and 13 <= hour <= 15:
            return False
        
        return True
    
    def _calculate_levels(self, direction: str, entry: float, atr: float, spread: float) -> Tuple[float, float, float]:
        """
        Calculate Stop Loss and Take Profit levels
        
        Returns:
            (sl_price, tp_price, rr_ratio)
        """
        # SL calculation
        sl_distance = max(DEFAULT_SL_PIPS * 0.01, atr * SL_ATR_MULTIPLIER)
        if SL_BUFFER_FOR_SPREAD:
            sl_distance += spread
        
        if direction == "BUY":
            sl_price = entry - sl_distance
        else:  # SELL
            sl_price = entry + sl_distance
        
        # TP calculation based on RR ratio
        tp_distance = sl_distance * TP_RR_RATIO
        
        if direction == "BUY":
            tp_price = entry + tp_distance
        else:  # SELL
            tp_price = entry - tp_distance
        
        # Calculate actual RR ratio
        rr_ratio = tp_distance / sl_distance
        
        return round(sl_price, 2), round(tp_price, 2), round(rr_ratio, 2)
    
    def update_trades(self, market_data: Dict[str, Any]) -> None:
        """
        Check open trades against current market data for SL/TP hit
        """
        current_price = market_data.get("current_price", 0)
        timestamp = market_data.get("timestamp", datetime.utcnow())
        
        # Get open trades
        open_trades = self.db.query(Trade).filter(Trade.status == TradeStatus.OPEN).all()
        
        for trade in open_trades:
            hit_type = None
            exit_price = None
            pips_gained = 0
            
            if trade.direction == TradeDirection.BUY:
                if current_price <= trade.sl_price:
                    hit_type = TradeStatus.CLOSED_LOSE
                    exit_price = trade.sl_price
                elif current_price >= trade.tp_price:
                    hit_type = TradeStatus.CLOSED_WIN
                    exit_price = trade.tp_price
            else:  # SELL
                if current_price >= trade.sl_price:
                    hit_type = TradeStatus.CLOSED_LOSE
                    exit_price = trade.sl_price
                elif current_price <= trade.tp_price:
                    hit_type = TradeStatus.CLOSED_WIN
                    exit_price = trade.tp_price
            
            if hit_type:
                # Calculate P/L
                pips_gained = self.calc.calculate_pips_to_level(trade.entry_price, exit_price)
                if trade.direction == TradeDirection.SELL:
                    pips_gained = -pips_gained
                
                pl_usd = pips_gained * 0.01 * LOT_SIZE * 100  # 0.01 lot = $1/pip
                
                # Update trade
                trade.status = hit_type
                trade.exit_price = exit_price
                trade.exit_timestamp_utc = timestamp
                trade.pips_gained = pips_gained
                trade.virtual_pl_usd = pl_usd
                
                # Update virtual balance
                self.virtual_balance += pl_usd
                if hit_type == TradeStatus.CLOSED_LOSE:
                    self.daily_loss += abs(pl_usd)
                
                self.db.commit()
                
                logger.info(f"Trade closed: {trade.signal_id} | {hit_type.value} | P/L: ${pl_usd:.2f}")

class RiskManager:
    """
    Risk management and position control
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_generate_signal(self) -> Tuple[bool, str]:
        """
        Check all risk conditions before allowing new signal
        
        Returns:
            (can_trade, reason)
        """
        # Check trade limit
        if not EVALUATION_MODE:
            trades_today = self._get_trades_today()
            if trades_today >= MAX_TRADES_PER_DAY:
                return False, f"Max trades ({MAX_TRADES_PER_DAY}) reached today"
        
        # Check daily loss limit
        daily_loss = self._get_daily_loss()
        loss_limit = VIRTUAL_INITIAL_BALANCE * (DAILY_LOSS_PERCENT / 100)
        if daily_loss >= loss_limit:
            return False, f"Daily loss limit (${loss_limit:.2f}) exceeded"
        
        # Check concurrent trades
        open_trades = self.db.query(Trade).filter(Trade.status == TradeStatus.OPEN).count()
        if open_trades >= MAX_CONCURRENT_TRADES:
            return False, f"Max concurrent trades ({MAX_CONCURRENT_TRADES}) reached"
        
        return True, "OK"
    
    def _get_trades_today(self) -> int:
        """Get number of trades created today (UTC)"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades = self.db.query(Trade).filter(Trade.created_at >= today_start).count()
        return trades
    
    def _get_daily_loss(self) -> float:
        """Get cumulative loss for today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        closed_trades = self.db.query(Trade).filter(
            Trade.created_at >= today_start,
            Trade.status.in_([TradeStatus.CLOSED_LOSE, TradeStatus.CLOSED_WIN])
        ).all()
        
        loss = sum(abs(t.virtual_pl_usd) for t in closed_trades if t.virtual_pl_usd < 0)
        return loss
