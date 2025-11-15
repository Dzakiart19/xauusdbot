"""
Unit Tests for Strategy Module
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.strategy import StrategyEngine, RiskManager
from data.db import SessionLocal, init_db
from data.models import Trade, TradeStatus, TradeDirection

class TestStrategy(unittest.TestCase):
    """Test strategy engine"""
    
    def setUp(self):
        """Initialize test database"""
        self.db = SessionLocal()
        init_db()
        self.engine = StrategyEngine(self.db)
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
    
    def test_signal_generation_no_data(self):
        """Test that signal is None with insufficient data"""
        market_data = {
            "m1_closes": [100],
            "m5_closes": [100],
            "m1_highs": [100],
            "m1_lows": [100],
            "m5_highs": [100],
            "m5_lows": [100],
            "m1_volumes": [1000],
            "current_price": 100,
            "bid": 99.99,
            "ask": 100.01,
            "timestamp": datetime.utcnow()
        }
        
        signal = self.engine.generate_signal(market_data)
        self.assertIsNone(signal)
    
    def test_sl_tp_calculation_buy(self):
        """Test SL/TP calculation for BUY"""
        sl, tp, rr = self.engine._calculate_levels("BUY", entry=2035.50, atr=0.50, spread=0.02)
        
        self.assertLess(sl, 2035.50)  # SL below entry
        self.assertGreater(tp, 2035.50)  # TP above entry
        self.assertGreater(rr, 1.0)  # RR ratio > 1
    
    def test_sl_tp_calculation_sell(self):
        """Test SL/TP calculation for SELL"""
        sl, tp, rr = self.engine._calculate_levels("SELL", entry=2035.50, atr=0.50, spread=0.02)
        
        self.assertGreater(sl, 2035.50)  # SL above entry
        self.assertLess(tp, 2035.50)  # TP below entry
        self.assertGreater(rr, 1.0)  # RR ratio > 1
    
    def test_session_filter_london_open(self):
        """Test London open time filtering"""
        london_time = datetime(2025, 11, 15, 8, 30)  # During London open
        result = self.engine._check_session_filter(london_time)
        self.assertFalse(result)
    
    def test_session_filter_normal_hours(self):
        """Test normal trading hours pass filter"""
        normal_time = datetime(2025, 11, 15, 12, 0)  # Normal hours
        result = self.engine._check_session_filter(normal_time)
        self.assertTrue(result)

class TestRiskManager(unittest.TestCase):
    """Test risk manager"""
    
    def setUp(self):
        """Initialize test database"""
        self.db = SessionLocal()
        init_db()
        self.risk_mgr = RiskManager(self.db)
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
    
    def test_can_generate_signal_ok(self):
        """Test that signal can be generated with no restrictions"""
        can_trade, reason = self.risk_mgr.can_generate_signal()
        self.assertTrue(can_trade)
        self.assertEqual(reason, "OK")
    
    def test_trades_today_count(self):
        """Test trade count tracking"""
        count = self.risk_mgr._get_trades_today()
        self.assertEqual(count, 0)
        
        # Add a trade
        trade = Trade(
            signal_id="test-signal",
            direction=TradeDirection.BUY,
            entry_price=2035.50,
            sl_price=2034.50,
            tp_price=2037.50,
            signal_timestamp_utc=datetime.utcnow(),
            confidence_score=75.0
        )
        self.db.add(trade)
        self.db.commit()
        
        count = self.risk_mgr._get_trades_today()
        self.assertEqual(count, 1)

if __name__ == "__main__":
    unittest.main()
