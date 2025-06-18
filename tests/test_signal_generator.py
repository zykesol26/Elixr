import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.signals.generator import SignalGenerator, TradingSignal

class TestSignalGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('builtins.open', create=True):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    'signals': {
                        'min_confidence': 0.75,
                        'risk_management': {
                            'max_daily_signals': 10,
                            'min_risk_reward_ratio': 2.0
                        },
                        'validation': {
                            'price_deviation_threshold': 0.05,
                            'timeframe_validation': True
                        }
                    }
                }
                self.generator = SignalGenerator()
    
    def test_generate_signal_valid_data(self):
        """Test signal generation with valid data."""
        analysis_result = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            'stop_loss': 48000.0,
            'take_profit': [52000.0, 54000.0],
            'confidence': 0.85,
            'timeframe': '1h',
            'reasoning': 'Strong bullish momentum'
        }
        
        signal = self.generator.generate_signal(analysis_result, 'test_tweet_id')
        
        self.assertIsNotNone(signal)
        if signal:  # Type guard
            self.assertEqual(signal.symbol, 'BTC/USDT')
            self.assertEqual(signal.direction, 'LONG')
            self.assertEqual(signal.entry_price, 50000.0)
            self.assertEqual(signal.confidence, 0.85)
    
    def test_generate_signal_missing_fields(self):
        """Test signal generation with missing required fields."""
        analysis_result = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            # Missing other required fields
        }
        
        signal = self.generator.generate_signal(analysis_result, 'test_tweet_id')
        
        self.assertIsNone(signal)
    
    def test_generate_signal_low_confidence(self):
        """Test signal generation with confidence below threshold."""
        analysis_result = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            'stop_loss': 48000.0,
            'take_profit': [52000.0, 54000.0],
            'confidence': 0.50,  # Below threshold
            'timeframe': '1h',
            'reasoning': 'Weak signal'
        }
        
        signal = self.generator.generate_signal(analysis_result, 'test_tweet_id')
        
        self.assertIsNone(signal)
    
    def test_generate_signal_invalid_price_levels(self):
        """Test signal generation with invalid price levels."""
        analysis_result = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            'stop_loss': 52000.0,  # Stop loss above entry price for LONG
            'take_profit': [48000.0, 46000.0],  # Take profit below entry
            'confidence': 0.85,
            'timeframe': '1h',
            'reasoning': 'Invalid price levels'
        }
        
        signal = self.generator.generate_signal(analysis_result, 'test_tweet_id')
        
        self.assertIsNone(signal)
    
    def test_generate_signal_invalid_timeframe(self):
        """Test signal generation with invalid timeframe."""
        analysis_result = {
            'symbol': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            'stop_loss': 48000.0,
            'take_profit': [52000.0, 54000.0],
            'confidence': 0.85,
            'timeframe': 'invalid_timeframe',
            'reasoning': 'Invalid timeframe'
        }
        
        signal = self.generator.generate_signal(analysis_result, 'test_tweet_id')
        
        self.assertIsNone(signal)

if __name__ == '__main__':
    unittest.main() 