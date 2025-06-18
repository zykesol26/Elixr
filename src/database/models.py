from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class MonitoredAccount(Base):
    __tablename__ = 'monitored_accounts'
    
    id = Column(Integer, primary_key=True)
    twitter_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tweets = relationship("ProcessedTweet", back_populates="account")

class ProcessedTweet(Base):
    __tablename__ = 'processed_tweets'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey('monitored_accounts.id'))
    content = Column(String, nullable=False)
    media_urls = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("MonitoredAccount", back_populates="tweets")
    signals = relationship("TradingSignal", back_populates="tweet")

class TradingSignal(Base):
    __tablename__ = 'trading_signals'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey('processed_tweets.id'))
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # LONG/SHORT
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(JSON, nullable=False)  # List of take profit levels
    confidence = Column(Float, nullable=False)
    timeframe = Column(String, nullable=False)
    reasoning = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Performance tracking
    is_executed = Column(Boolean, default=False)
    execution_price = Column(Float)
    execution_time = Column(DateTime)
    is_closed = Column(Boolean, default=False)
    close_price = Column(Float)
    close_time = Column(DateTime)
    pnl = Column(Float)
    
    tweet = relationship("ProcessedTweet", back_populates="signals")

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    notification_settings = Column(JSON, default={
        'signals': True,
        'updates': True,
        'alerts': True
    })
    trading_pairs = Column(JSON, default=[])  # List of preferred trading pairs
    risk_level = Column(String, default='medium')  # low/medium/high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db(database_url: str):
    """Initialize the database with all tables."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine 