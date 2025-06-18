import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Base, MonitoredAccount, UserPreference
from sqlalchemy import create_engine

def init_database():
    """Initialize the database with default data."""
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Create database engine
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add default monitored accounts
        default_accounts = [
            MonitoredAccount(
                twitter_id="123456789",
                username="trader1",
                is_active=True
            ),
            MonitoredAccount(
                twitter_id="987654321",
                username="trader2",
                is_active=True
            )
        ]
        
        for account in default_accounts:
            # Check if account already exists
            existing = session.query(MonitoredAccount).filter_by(
                twitter_id=account.twitter_id
            ).first()
            
            if not existing:
                session.add(account)
        
        # Add default user preferences
        default_preferences = UserPreference(
            telegram_id="123456789",
            is_active=True,
            notification_settings={
                'signals': True,
                'updates': True,
                'alerts': True
            },
            trading_pairs=['BTC/USDT', 'ETH/USDT'],
            risk_level='medium'
        )
        
        # Check if preferences already exist
        existing = session.query(UserPreference).filter_by(
            telegram_id=default_preferences.telegram_id
        ).first()
        
        if not existing:
            session.add(default_preferences)
        
        # Commit changes
        session.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {str(e)}")
        raise
    
    finally:
        session.close()

if __name__ == "__main__":
    init_database() 