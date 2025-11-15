"""
Unit Tests for Indicators Module
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.indicators import IndicatorCalculator

class TestIndicators(unittest.TestCase):
    """Test indicator calculations"""
    
    def setUp(self):
        self.calc = IndicatorCalculator()
    
    def test_ema_calculation(self):
        """Test EMA calculation"""
        prices = [100, 102, 101, 103, 104, 102, 105, 106, 104, 107]
        ema_values = self.calc.calculate_ema(prices, period=3)
        
        # Should have NaN for first (period-1) values
        self.assertTrue(float('nan') in [v for v in ema_values[:2] if isinstance(v, float) and v != v])
        
        # Last value should be numeric
        self.assertIsNotNone(ema_values[-1])
        self.assertTrue(100 < ema_values[-1] < 110)
    
    def test_ema_alignment(self):
        """Test EMA trend alignment"""
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]  # Uptrend
        alignment = self.calc.get_ema_alignment(prices, 3, 5, 7)
        self.assertEqual(alignment, "BULLISH")
        
        prices = [109, 108, 107, 106, 105, 104, 103, 102, 101, 100]  # Downtrend
        alignment = self.calc.get_ema_alignment(prices, 3, 5, 7)
        self.assertEqual(alignment, "BEARISH")
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        prices = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
                  46.08, 45.89, 46.03, 45.61, 46.28, 46.00, 46.03, 46.41, 46.89, 47.00]
        rsi_values = self.calc.calculate_rsi(prices, period=14)
        
        # Should have RSI values in 0-100 range (after warm-up)
        valid_rsi = [v for v in rsi_values if not (isinstance(v, float) and v != v)]
        if valid_rsi:
            for rsi in valid_rsi[-3:]:
                self.assertTrue(0 <= rsi <= 100)
    
    def test_rsi_oversold(self):
        """Test RSI oversold detection"""
        self.assertTrue(self.calc.is_rsi_oversold(25, threshold=30))
        self.assertFalse(self.calc.is_rsi_oversold(35, threshold=30))
    
    def test_rsi_overbought(self):
        """Test RSI overbought detection"""
        self.assertTrue(self.calc.is_rsi_overbought(75, threshold=70))
        self.assertFalse(self.calc.is_rsi_overbought(65, threshold=70))
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        highs = [102, 103, 104, 103, 105, 106, 105, 107, 108, 109]
        lows = [100, 101, 102, 101, 103, 104, 103, 105, 106, 107]
        closes = [101, 102, 103, 102, 104, 105, 104, 106, 107, 108]
        
        atr_values = self.calc.calculate_atr(highs, lows, closes, period=5)
        
        # Should have numeric ATR values
        valid_atr = [v for v in atr_values if not (isinstance(v, float) and v != v)]
        self.assertGreater(len(valid_atr), 0)
        
        # ATR should be positive
        for atr in valid_atr:
            self.assertGreater(atr, 0)
    
    def test_volume_sma(self):
        """Test volume SMA calculation"""
        volumes = [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500]
        vol_sma = self.calc.calculate_volume_sma(volumes, period=3)
        
        # Should have SMA values
        self.assertGreater(len(vol_sma), 0)
        
        # SMA should be close to average volume
        self.assertTrue(1000 <= vol_sma[-1] <= 1500)
    
    def test_volume_spike(self):
        """Test volume spike detection"""
        avg_vol = 1000
        self.assertTrue(self.calc.is_volume_spike(1600, avg_vol, 1.5))
        self.assertFalse(self.calc.is_volume_spike(1400, avg_vol, 1.5))
    
    def test_pips_calculation(self):
        """Test pips calculation"""
        pips = self.calc.calculate_pips_to_level(2035.50, 2036.00)
        self.assertEqual(pips, 50.0)
        
        pips = self.calc.calculate_pips_to_level(2035.50, 2035.00)
        self.assertEqual(pips, -50.0)

if __name__ == "__main__":
    unittest.main()
