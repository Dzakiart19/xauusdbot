"""
Backtester - CSV Replay Engine for Performance Analysis
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from config.strategy import StrategyEngine, RiskManager
from data.db import SessionLocal, init_db
from utils.indicators import IndicatorCalculator
from utils.logger import get_logger

logger = get_logger()

class Backtester:
    """
    CSV replay backtester for XAUUSD trading signals
    """
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.db = SessionLocal()
        self.strategy = StrategyEngine(self.db)
        self.risk_mgr = RiskManager(self.db)
        self.trades = []
        self.results = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "total_pips": 0,
            "total_pl_usd": 0,
            "max_drawdown": 0,
            "avg_rr": 0,
            "profit_factor": 0,
        }
    
    def load_csv(self) -> List[Dict[str, Any]]:
        """
        Load OHLCV data from CSV
        Expected columns: timestamp,open,high,low,close,volume
        """
        data = []
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append({
                        "timestamp": row["timestamp"],
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": int(row["volume"])
                    })
            logger.info(f"Loaded {len(data)} candles from {self.csv_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}")
            return []
    
    def run(self) -> Dict[str, Any]:
        """
        Run backtesting on loaded CSV data
        """
        data = self.load_csv()
        if not data:
            return self.results
        
        # Separate into M1 and M5 (assuming CSV is M1, aggregate M5)
        m1_data = data
        
        print(f"\n{'='*60}")
        print(f"Backtesting {self.csv_file}")
        print(f"Candles: {len(m1_data)}")
        print(f"{'='*60}\n")
        
        for i, candle in enumerate(m1_data):
            # Prepare market data for strategy
            m1_closes = [c["close"] for c in m1_data[max(0, i-50):i+1]]
            m1_highs = [c["high"] for c in m1_data[max(0, i-50):i+1]]
            m1_lows = [c["low"] for c in m1_data[max(0, i-50):i+1]]
            m1_volumes = [c["volume"] for c in m1_data[max(0, i-50):i+1]]
            
            market_data = {
                "m1_closes": m1_closes,
                "m5_closes": m1_closes,  # Use M1 for both (can be improved)
                "m1_highs": m1_highs,
                "m1_lows": m1_lows,
                "m5_highs": m1_highs,
                "m5_lows": m1_lows,
                "m1_volumes": m1_volumes,
                "current_price": candle["close"],
                "bid": candle["close"] - 0.02,
                "ask": candle["close"] + 0.02,
                "timestamp": datetime.fromisoformat(candle["timestamp"])
            }
            
            # Check if we can trade
            can_trade, _ = self.risk_mgr.can_generate_signal()
            if can_trade:
                # Generate signal
                signal = self.strategy.generate_signal(market_data)
                if signal:
                    self.trades.append(signal)
            
            # Update open trades
            self.strategy.update_trades(market_data)
        
        # Calculate statistics
        self._calculate_stats()
        self._print_report()
        
        return self.results
    
    def _calculate_stats(self) -> None:
        """Calculate performance statistics"""
        from data.models import Trade, TradeStatus
        
        closed_trades = self.db.query(Trade).filter(
            Trade.status.in_([TradeStatus.CLOSED_LOSE, TradeStatus.CLOSED_WIN])
        ).all()
        
        self.results["total_trades"] = len(closed_trades)
        
        wins = [t for t in closed_trades if t.status == TradeStatus.CLOSED_WIN]
        losses = [t for t in closed_trades if t.status == TradeStatus.CLOSED_LOSE]
        
        self.results["wins"] = len(wins)
        self.results["losses"] = len(losses)
        
        if closed_trades:
            self.results["win_rate"] = (len(wins) / len(closed_trades)) * 100
        
        # Total P/L
        total_pl = sum(t.virtual_pl_usd or 0 for t in closed_trades)
        self.results["total_pl_usd"] = total_pl
        
        # Total pips
        total_pips = sum(t.pips_gained or 0 for t in closed_trades)
        self.results["total_pips"] = total_pips
        
        # Profit factor
        win_pl = sum(t.virtual_pl_usd or 0 for t in wins)
        loss_pl = sum(abs(t.virtual_pl_usd or 0) for t in losses)
        self.results["profit_factor"] = win_pl / loss_pl if loss_pl > 0 else 0
        
        # Average R/R
        rr_ratios = []
        for t in closed_trades:
            if t.sl_price and t.tp_price:
                if t.direction.value == "BUY":
                    rr = (t.tp_price - t.entry_price) / (t.entry_price - t.sl_price)
                else:
                    rr = (t.entry_price - t.tp_price) / (t.sl_price - t.entry_price)
                rr_ratios.append(rr)
        
        self.results["avg_rr"] = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
    
    def _print_report(self) -> None:
        """Print backtesting report"""
        print(f"\n{'='*60}")
        print("BACKTESTING RESULTS")
        print(f"{'='*60}")
        print(f"Total Trades: {self.results['total_trades']}")
        print(f"Wins: {self.results['wins']} | Losses: {self.results['losses']}")
        print(f"Win Rate: {self.results['win_rate']:.2f}%")
        print(f"Total P/L: ${self.results['total_pl_usd']:.2f}")
        print(f"Total Pips: {self.results['total_pips']:.2f}")
        print(f"Profit Factor: {self.results['profit_factor']:.2f}")
        print(f"Avg R/R: {self.results['avg_rr']:.2f}")
        print(f"{'='*60}\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="XAUUSD Strategy Backtester"
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to CSV file with OHLCV data"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="scalping_m1_m5",
        help="Strategy name"
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=1000000,
        help="Initial virtual capital (default: 1000000)"
    )
    parser.add_argument(
        "--lot-size",
        type=float,
        default=0.01,
        help="Lot size (default: 0.01)"
    )
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Run backtester
    backtester = Backtester(args.data)
    backtester.run()

if __name__ == "__main__":
    main()
