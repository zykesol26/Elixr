import os
import logging
from dotenv import load_dotenv
from src.twitter.monitor import TwitterMonitor
from src.ai.analyzer import ContentAnalyzer
from src.signals.generator import SignalGenerator
from src.telegram.bot import TradingBot
from src.database.models import init_db
from src.database.operations import DatabaseOperations
import yaml
import asyncio
import signal
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingSignalBot:
    def __init__(self):
        # Load configuration
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize database operations
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        self.db_ops = DatabaseOperations(database_url)
        
        # Initialize components
        twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not twitter_token:
            raise ValueError("TWITTER_BEARER_TOKEN environment variable is not set")
        
        self.twitter_monitor = TwitterMonitor(
            bearer_token=twitter_token
        )
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.content_analyzer = ContentAnalyzer(
            api_key=openai_key
        )
        
        self.signal_generator = SignalGenerator()
        
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        
        self.telegram_bot = TradingBot(
            token=telegram_token,
            database_ops=self.db_ops
        )
        
        # Initialize database
        self.db_engine = init_db(database_url)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Received shutdown signal, stopping bot...")
        self.stop()
        sys.exit(0)
    
    def stop(self):
        """Stop the bot and cleanup resources."""
        try:
            if hasattr(self, 'twitter_monitor'):
                self.twitter_monitor.stop_polling()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
    
    async def process_tweet(self, tweet_data: dict):
        """Process a new tweet and generate signals if applicable."""
        try:
            logger.info(f"Processing tweet: {tweet_data['tweet_id']}")
            
            # Check if tweet already processed
            existing_tweet = self.db_ops.get_tweet_by_id(tweet_data['tweet_id'])
            if existing_tweet:
                logger.info(f"Tweet {tweet_data['tweet_id']} already processed, skipping")
                return
            
            # Get account ID for the tweet author
            # For now, we'll use a default account ID (you can enhance this)
            account_id = 1  # Default monitored account
            
            # Store tweet in database
            processed_tweet = self.db_ops.add_processed_tweet(
                tweet_id=tweet_data['tweet_id'],
                account_id=account_id,
                content=tweet_data['text'],
                media_urls=[tweet_data['media']['url']] if tweet_data.get('media') and tweet_data['media'].get('url') else None
            )
            
            # Analyze content
            analysis_result = self.content_analyzer.analyze_text(tweet_data['text'])
            
            # If media is present, analyze it
            if tweet_data.get('media'):
                if tweet_data['media']['type'] == 'photo':
                    media_analysis = self.content_analyzer.analyze_image(
                        tweet_data['media']['url']
                    )
                    # Merge media analysis with text analysis
                    analysis_result.update(media_analysis)
                elif tweet_data['media']['type'] == 'video':
                    media_analysis = self.content_analyzer.analyze_video(
                        tweet_data['media']['url']
                    )
                    analysis_result.update(media_analysis)
            
            # Generate trading signal
            signal = self.signal_generator.generate_signal(
                analysis_result,
                tweet_data['tweet_id']
            )
            
            if signal:
                # Store signal in database
                signal_data = {
                    'symbol': signal.symbol,
                    'direction': signal.direction,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'confidence': signal.confidence,
                    'timeframe': signal.timeframe,
                    'reasoning': signal.reasoning
                }
                
                stored_signal = self.db_ops.add_trading_signal(signal_data, processed_tweet.id)  # type: ignore
                
                # Send signal to Telegram subscribers
                await self.telegram_bot.send_trading_signal(signal_data)
                
                logger.info(f"Generated and sent signal for {signal.symbol}")
            else:
                logger.info(f"No valid signal generated for tweet {tweet_data['tweet_id']}")
            
        except Exception as e:
            logger.error(f"Error processing tweet: {str(e)}")
    
    def tweet_callback(self, tweet_data: dict):
        """Callback function for new tweets from Twitter stream."""
        try:
            # Run the async process_tweet function
            asyncio.create_task(self.process_tweet(tweet_data))
        except Exception as e:
            logger.error(f"Error in tweet callback: {str(e)}")
    
    def run(self):
        """Start the bot and its components."""
        try:
            logger.info("Starting Crypto Trading Signal Bot...")
            
            # Start Twitter monitoring
            monitored_accounts = [
                account['id'] for account in self.config['twitter']['monitored_accounts']
            ]
            
            # Start polling for new tweets
            self.twitter_monitor.start_polling(monitored_accounts, self.tweet_callback)
            
            logger.info("Twitter polling started successfully")
            
            # Start Telegram bot
            logger.info("Starting Telegram bot...")
            self.telegram_bot.run()
            
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            self.stop()
            raise

if __name__ == "__main__":
    try:
        bot = TradingSignalBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1) 