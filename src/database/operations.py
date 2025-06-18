import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, desc
from datetime import datetime, timedelta
from .models import Base, MonitoredAccount, ProcessedTweet, TradingSignal, UserPreference

logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    # MonitoredAccount operations
    def add_monitored_account(self, twitter_id: str, username: str) -> MonitoredAccount:
        """Add a new monitored Twitter account."""
        session = self.get_session()
        try:
            account = MonitoredAccount(
                twitter_id=twitter_id,
                username=username,
                is_active=True
            )
            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding monitored account: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_monitored_accounts(self) -> List[MonitoredAccount]:
        """Get all active monitored accounts."""
        session = self.get_session()
        try:
            return session.query(MonitoredAccount).filter_by(is_active=True).all()
        finally:
            session.close()
    
    # ProcessedTweet operations
    def add_processed_tweet(self, tweet_id: str, account_id: int, content: str, media_urls: Optional[List[str]] = None) -> ProcessedTweet:
        """Add a processed tweet to the database."""
        session = self.get_session()
        try:
            tweet = ProcessedTweet(
                tweet_id=tweet_id,
                account_id=account_id,
                content=content,
                media_urls=media_urls or []
            )
            session.add(tweet)
            session.commit()
            session.refresh(tweet)
            return tweet
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding processed tweet: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_tweet_by_id(self, tweet_id: str) -> Optional[ProcessedTweet]:
        """Get a processed tweet by its Twitter ID."""
        session = self.get_session()
        try:
            return session.query(ProcessedTweet).filter_by(tweet_id=tweet_id).first()
        finally:
            session.close()
    
    # TradingSignal operations
    def add_trading_signal(self, signal_data: Dict, tweet_id: int) -> TradingSignal:
        """Add a new trading signal to the database."""
        session = self.get_session()
        try:
            signal = TradingSignal(
                tweet_id=tweet_id,
                symbol=signal_data['symbol'],
                direction=signal_data['direction'],
                entry_price=signal_data['entry_price'],
                stop_loss=signal_data['stop_loss'],
                take_profit=signal_data['take_profit'],
                confidence=signal_data['confidence'],
                timeframe=signal_data['timeframe'],
                reasoning=signal_data['reasoning']
            )
            session.add(signal)
            session.commit()
            session.refresh(signal)
            return signal
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding trading signal: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_recent_signals(self, limit: int = 10) -> List[TradingSignal]:
        """Get recent trading signals."""
        session = self.get_session()
        try:
            return session.query(TradingSignal).order_by(desc(TradingSignal.created_at)).limit(limit).all()
        finally:
            session.close()
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 10) -> List[TradingSignal]:
        """Get recent signals for a specific symbol."""
        session = self.get_session()
        try:
            return session.query(TradingSignal).filter_by(symbol=symbol).order_by(desc(TradingSignal.created_at)).limit(limit).all()
        finally:
            session.close()
    
    def update_signal_execution(self, signal_id: int, execution_price: float):
        """Update signal with execution details."""
        session = self.get_session()
        try:
            signal = session.query(TradingSignal).filter_by(id=signal_id).first()
            if signal:
                signal.is_executed = True  # type: ignore
                signal.execution_price = execution_price  # type: ignore
                signal.execution_time = datetime.utcnow()  # type: ignore
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating signal execution: {str(e)}")
            raise
        finally:
            session.close()
    
    def close_signal(self, signal_id: int, close_price: float, pnl: float):
        """Close a trading signal with P&L."""
        session = self.get_session()
        try:
            signal = session.query(TradingSignal).filter_by(id=signal_id).first()
            if signal:
                signal.is_closed = True  # type: ignore
                signal.close_price = close_price  # type: ignore
                signal.close_time = datetime.utcnow()  # type: ignore
                signal.pnl = pnl  # type: ignore
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error closing signal: {str(e)}")
            raise
        finally:
            session.close()
    
    # UserPreference operations
    def add_user_preference(self, telegram_id: str, trading_pairs: Optional[List[str]] = None, risk_level: str = 'medium') -> UserPreference:
        """Add or update user preferences."""
        session = self.get_session()
        try:
            existing = session.query(UserPreference).filter_by(telegram_id=telegram_id).first()
            if existing:
                if trading_pairs is not None:
                    existing.trading_pairs = trading_pairs  # type: ignore
                existing.risk_level = risk_level  # type: ignore
                existing.updated_at = datetime.utcnow()  # type: ignore
                session.commit()
                session.refresh(existing)
                return existing
            else:
                preference = UserPreference(
                    telegram_id=telegram_id,
                    trading_pairs=trading_pairs or [],
                    risk_level=risk_level
                )
                session.add(preference)
                session.commit()
                session.refresh(preference)
                return preference
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding user preference: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_user_preference(self, telegram_id: str) -> Optional[UserPreference]:
        """Get user preferences by Telegram ID."""
        session = self.get_session()
        try:
            return session.query(UserPreference).filter_by(telegram_id=telegram_id).first()
        finally:
            session.close()
    
    def get_active_users(self) -> List[UserPreference]:
        """Get all active users."""
        session = self.get_session()
        try:
            return session.query(UserPreference).filter_by(is_active=True).all()
        finally:
            session.close()
    
    def update_notification_settings(self, telegram_id: str, settings: Dict):
        """Update user notification settings."""
        session = self.get_session()
        try:
            user = session.query(UserPreference).filter_by(telegram_id=telegram_id).first()
            if user:
                user.notification_settings.update(settings)
                user.updated_at = datetime.utcnow()  # type: ignore
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating notification settings: {str(e)}")
            raise
        finally:
            session.close()
    
    # Analytics operations
    def get_signal_statistics(self, days: int = 30) -> Dict:
        """Get signal statistics for the last N days."""
        session = self.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            total_signals = session.query(TradingSignal).filter(
                TradingSignal.created_at >= start_date
            ).count()
            
            executed_signals = session.query(TradingSignal).filter(
                TradingSignal.created_at >= start_date,
                TradingSignal.is_executed == True
            ).count()
            
            closed_signals = session.query(TradingSignal).filter(
                TradingSignal.created_at >= start_date,
                TradingSignal.is_closed == True
            ).count()
            
            profitable_signals = session.query(TradingSignal).filter(
                TradingSignal.created_at >= start_date,
                TradingSignal.is_closed == True,
                TradingSignal.pnl > 0
            ).count()
            
            return {
                'total_signals': total_signals,
                'executed_signals': executed_signals,
                'closed_signals': closed_signals,
                'profitable_signals': profitable_signals,
                'success_rate': (profitable_signals / closed_signals * 100) if closed_signals > 0 else 0
            }
        finally:
            session.close() 