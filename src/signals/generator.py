import logging
from typing import Dict, List, Optional
from datetime import datetime
import yaml
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    symbol: str
    direction: str  # LONG/SHORT
    entry_price: float
    stop_loss: float
    take_profit: List[float]
    confidence: float
    timeframe: str
    source_tweet: str
    reasoning: str
    created_at: datetime = datetime.now()

class SignalGenerator:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.min_confidence = self.config['signals']['min_confidence']
        self.risk_management = self.config['signals']['risk_management']
        self.validation = self.config['signals']['validation']
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_signal(self, analysis_result: Dict, source_tweet: str) -> Optional[TradingSignal]:
        """Generate a trading signal from AI analysis results."""
        try:
            # Validate required fields
            required_fields = ['symbol', 'direction', 'entry_price', 'stop_loss', 
                             'take_profit', 'confidence', 'timeframe', 'reasoning']
            
            if not all(field in analysis_result for field in required_fields):
                logger.warning("Missing required fields in analysis result")
                return None
            
            # Create signal object
            signal = TradingSignal(
                symbol=analysis_result['symbol'],
                direction=analysis_result['direction'],
                entry_price=float(analysis_result['entry_price']),
                stop_loss=float(analysis_result['stop_loss']),
                take_profit=[float(tp) for tp in analysis_result['take_profit']],
                confidence=float(analysis_result['confidence']),
                timeframe=analysis_result['timeframe'],
                source_tweet=source_tweet,
                reasoning=analysis_result['reasoning']
            )
            
            # Validate signal
            if not self._validate_signal(signal):
                return None
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return None
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal against various criteria."""
        try:
            # Check confidence threshold
            if signal.confidence < self.min_confidence:
                logger.info(f"Signal confidence {signal.confidence} below threshold {self.min_confidence}")
                return False
            
            # Validate price levels
            if not self._validate_price_levels(signal):
                return False
            
            # Validate risk-reward ratio
            if not self._validate_risk_reward(signal):
                return False
            
            # Validate timeframe
            if self.validation['timeframe_validation']:
                if not self._validate_timeframe(signal.timeframe):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False
    
    def _validate_price_levels(self, signal: TradingSignal) -> bool:
        """Validate price levels and their relationships."""
        try:
            # Check if entry price is between stop loss and take profit
            if signal.direction == "LONG":
                if not (signal.stop_loss < signal.entry_price < min(signal.take_profit)):
                    logger.info("Invalid price levels for LONG position")
                    return False
            else:  # SHORT
                if not (max(signal.take_profit) < signal.entry_price < signal.stop_loss):
                    logger.info("Invalid price levels for SHORT position")
                    return False
            
            # Check price deviation
            price_deviation = abs(signal.entry_price - signal.stop_loss) / signal.entry_price
            if price_deviation > self.validation['price_deviation_threshold']:
                logger.info(f"Price deviation {price_deviation} exceeds threshold")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating price levels: {str(e)}")
            return False
    
    def _validate_risk_reward(self, signal: TradingSignal) -> bool:
        """Validate risk-reward ratio."""
        try:
            if signal.direction == "LONG":
                risk = signal.entry_price - signal.stop_loss
                reward = min(signal.take_profit) - signal.entry_price
            else:  # SHORT
                risk = signal.stop_loss - signal.entry_price
                reward = signal.entry_price - max(signal.take_profit)
            
            if risk <= 0 or reward <= 0:
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < self.risk_management['min_risk_reward_ratio']:
                logger.info(f"Risk-reward ratio {risk_reward_ratio} below minimum")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating risk-reward ratio: {str(e)}")
            return False
    
    def _validate_timeframe(self, timeframe: str) -> bool:
        """Validate trading timeframe."""
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        return timeframe.lower() in valid_timeframes 