"""
Technical Indicators Calculation Engine
EMA, RSI, Stochastic, ATR, Volume calculations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from collections import deque

class IndicatorCalculator:
    """Calculate technical indicators for OHLCV data"""
    
    def __init__(self, max_bars: int = 500):
        """
        Initialize indicator calculator with circular buffer
        
        Args:
            max_bars: Maximum number of bars to store in memory (for RAM efficiency)
        """
        self.max_bars = max_bars
        self.data_buffer = deque(maxlen=max_bars)
    
    def add_candle(self, candle: Dict) -> None:
        """Add new candle to buffer"""
        self.data_buffer.append(candle)
    
    def get_dataframe(self) -> pd.DataFrame:
        """Convert buffer to pandas DataFrame"""
        if not self.data_buffer:
            return pd.DataFrame()
        return pd.DataFrame(list(self.data_buffer))
    
    # ===== EMA CALCULATION =====
    def calculate_ema(self, values: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average
        
        Args:
            values: List of prices
            period: EMA period (e.g., 5, 10, 20)
        
        Returns:
            List of EMA values (same length as input, first (period-1) are NaN)
        """
        if len(values) < period:
            return [np.nan] * len(values)
        
        ema_values = [np.nan] * (period - 1)
        multiplier = 2 / (period + 1)
        
        # SMA for first EMA value
        sma = np.mean(values[:period])
        ema = sma
        ema_values.append(ema)
        
        # Calculate subsequent EMAs
        for i in range(period, len(values)):
            ema = values[i] * multiplier + ema * (1 - multiplier)
            ema_values.append(ema)
        
        return ema_values
    
    def get_ema_alignment(self, close_prices: List[float], 
                         ema_fast: int, ema_med: int, ema_slow: int) -> str:
        """
        Check EMA alignment for trend confirmation
        
        Returns:
            "BULLISH" if fast > mid > slow
            "BEARISH" if fast < mid < slow
            "NEUTRAL" otherwise
        """
        if len(close_prices) < ema_slow:
            return "NEUTRAL"
        
        ema_fast_vals = self.calculate_ema(close_prices, ema_fast)
        ema_med_vals = self.calculate_ema(close_prices, ema_med)
        ema_slow_vals = self.calculate_ema(close_prices, ema_slow)
        
        if np.isnan(ema_fast_vals[-1]) or np.isnan(ema_med_vals[-1]) or np.isnan(ema_slow_vals[-1]):
            return "NEUTRAL"
        
        fast_val = ema_fast_vals[-1]
        med_val = ema_med_vals[-1]
        slow_val = ema_slow_vals[-1]
        
        if fast_val > med_val > slow_val:
            return "BULLISH"
        elif fast_val < med_val < slow_val:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    # ===== RSI CALCULATION =====
    def calculate_rsi(self, values: List[float], period: int = 14) -> List[float]:
        """
        Calculate Relative Strength Index
        
        Args:
            values: List of prices
            period: RSI period (default 14)
        
        Returns:
            List of RSI values (0-100)
        """
        if len(values) < period + 1:
            return [np.nan] * len(values)
        
        deltas = np.diff(values)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros(len(values))
        avg_losses = np.zeros(len(values))
        
        # Initial averages
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])
        
        # Smoothed averages
        for i in range(period + 1, len(values)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        # Calculate RSI
        rs = np.divide(avg_gains, avg_losses, where=avg_losses != 0, out=np.zeros_like(avg_losses))
        rsi = 100 - (100 / (1 + rs))
        
        return [np.nan] * period + list(rsi[period:])
    
    def is_rsi_oversold(self, rsi_value: float, threshold: int = 30) -> bool:
        """Check if RSI is oversold"""
        return not np.isnan(rsi_value) and rsi_value < threshold
    
    def is_rsi_overbought(self, rsi_value: float, threshold: int = 70) -> bool:
        """Check if RSI is overbought"""
        return not np.isnan(rsi_value) and rsi_value > threshold
    
    # ===== STOCHASTIC CALCULATION =====
    def calculate_stochastic(self, high_prices: List[float], low_prices: List[float], 
                            close_prices: List[float], period: int = 14, 
                            k_smooth: int = 3, d_smooth: int = 3) -> Tuple[List[float], List[float]]:
        """
        Calculate Stochastic Oscillator (%K, %D)
        
        Returns:
            Tuple of (stoch_k_values, stoch_d_values)
        """
        if len(close_prices) < period:
            return [np.nan] * len(close_prices), [np.nan] * len(close_prices)
        
        # Calculate raw %K
        k_raw = []
        for i in range(period - 1, len(close_prices)):
            high_slice = high_prices[i - period + 1:i + 1]
            low_slice = low_prices[i - period + 1:i + 1]
            highest_high = max(high_slice)
            lowest_low = min(low_slice)
            
            if highest_high - lowest_low == 0:
                k_raw.append(50.0)
            else:
                k = 100 * (close_prices[i] - lowest_low) / (highest_high - lowest_low)
                k_raw.append(k)
        
        # Smooth %K with SMA
        k_smoothed = self._simple_moving_average(k_raw, k_smooth)
        stoch_k = [np.nan] * (period - 1) + k_smoothed
        
        # Calculate %D (SMA of smoothed %K)
        if len(k_smoothed) < d_smooth:
            stoch_d = [np.nan] * len(stoch_k)
        else:
            d_raw = self._simple_moving_average(k_smoothed, d_smooth)
            stoch_d = [np.nan] * (period - 1 + k_smooth - 1) + d_raw
        
        return stoch_k[:len(close_prices)], stoch_d[:len(close_prices)]
    
    def is_stoch_oversold(self, k_value: float, threshold: int = 20) -> bool:
        """Check if Stochastic is oversold"""
        return not np.isnan(k_value) and k_value < threshold
    
    def is_stoch_overbought(self, k_value: float, threshold: int = 80) -> bool:
        """Check if Stochastic is overbought"""
        return not np.isnan(k_value) and k_value > threshold
    
    # ===== ATR CALCULATION =====
    def calculate_atr(self, high_prices: List[float], low_prices: List[float], 
                     close_prices: List[float], period: int = 14) -> List[float]:
        """
        Calculate Average True Range
        
        Returns:
            List of ATR values
        """
        if len(high_prices) < 2:
            return [np.nan] * len(high_prices)
        
        # Calculate True Range
        tr_list = []
        for i in range(len(high_prices)):
            if i == 0:
                tr = high_prices[i] - low_prices[i]
            else:
                tr1 = high_prices[i] - low_prices[i]
                tr2 = abs(high_prices[i] - close_prices[i - 1])
                tr3 = abs(low_prices[i] - close_prices[i - 1])
                tr = max(tr1, tr2, tr3)
            tr_list.append(tr)
        
        # Calculate ATR using SMA
        atr = self._simple_moving_average(tr_list, period)
        return [np.nan] * (period - 1) + atr
    
    # ===== VOLUME ANALYSIS =====
    def calculate_volume_sma(self, volumes: List[int], period: int = 20) -> List[float]:
        """Calculate Volume SMA"""
        return self._simple_moving_average(volumes, period)
    
    def is_volume_spike(self, current_volume: int, avg_volume: float, multiplier: float = 1.5) -> bool:
        """Check if current volume exceeds average by multiplier"""
        return current_volume > (avg_volume * multiplier)
    
    # ===== HELPER FUNCTIONS =====
    def _simple_moving_average(self, values: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        if len(values) < period:
            return []
        
        sma = []
        for i in range(period - 1, len(values)):
            sma.append(np.mean(values[i - period + 1:i + 1]))
        return sma
    
    def calculate_pips_to_level(self, current_price: float, target_price: float) -> float:
        """
        Calculate pips from current price to target
        For XAUUSD: 1 pip = 0.01
        """
        pips = (target_price - current_price) / 0.01
        return round(pips, 2)

# Global calculator instance
indicator_calc = IndicatorCalculator()
