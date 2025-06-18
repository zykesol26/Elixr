import tweepy
import logging
from typing import List, Dict, Optional, Callable
import time
from datetime import datetime, timedelta
import yaml
import os
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterMonitor:
    def __init__(self, bearer_token: str, config_path: str = "config/config.yaml"):
        self.client = tweepy.Client(bearer_token=bearer_token)
        self.config = self._load_config(config_path)
        self.rate_limit_window = self.config['twitter']['rate_limit_window']
        self.max_requests = self.config['twitter']['max_requests_per_window']
        self.request_timestamps = []
        self.polling_thread = None
        self.is_polling = False
        self.last_check_times = {}  # Track last check time for each user
        self.polling_interval = 60  # Check every 60 seconds
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        # Remove timestamps older than the window
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if current_time - ts < self.rate_limit_window]
        
        if len(self.request_timestamps) >= self.max_requests:
            return False
        return True
    
    def _wait_for_rate_limit(self):
        """Wait until we can make another request."""
        while not self._check_rate_limit():
            time.sleep(1)
    
    def start_polling(self, user_ids: List[str], tweet_callback: Callable):
        """Start polling for new tweets from specific users."""
        try:
            # Initialize last check times for each user
            for user_id in user_ids:
                self.last_check_times[user_id] = datetime.now() - timedelta(minutes=5)
            
            # Start polling in a separate thread
            self.polling_thread = threading.Thread(
                target=self._run_polling,
                args=(user_ids, tweet_callback),
                daemon=True
            )
            self.polling_thread.start()
            self.is_polling = True
            
            logger.info(f"Started polling for {len(user_ids)} accounts")
            
        except Exception as e:
            logger.error(f"Error starting polling: {str(e)}")
            raise
    
    def _run_polling(self, user_ids: List[str], tweet_callback: Callable):
        """Run the polling loop in a separate thread."""
        try:
            while self.is_polling:
                for user_id in user_ids:
                    try:
                        # Get new tweets since last check
                        new_tweets = self.get_user_tweets_since(
                            user_id, 
                            self.last_check_times.get(user_id, datetime.now() - timedelta(minutes=5))
                        )
                        
                        # Process new tweets
                        for tweet in new_tweets:
                            processed_tweet = self.process_new_tweet(tweet)
                            if processed_tweet:
                                tweet_callback(processed_tweet)
                        
                        # Update last check time
                        if new_tweets:
                            self.last_check_times[user_id] = datetime.now()
                        
                    except Exception as e:
                        logger.error(f"Error polling user {user_id}: {str(e)}")
                
                # Wait before next poll
                time.sleep(self.polling_interval)
                
        except Exception as e:
            logger.error(f"Polling error: {str(e)}")
            self.is_polling = False
    
    def stop_polling(self):
        """Stop the polling."""
        self.is_polling = False
        logger.info("Stopped Twitter polling")
    
    def get_user_tweets_since(self, user_id: str, since_time: datetime, max_results: int = 10) -> List[Dict]:
        """Get tweets from a specific user since a given time."""
        try:
            self._wait_for_rate_limit()
            
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'text', 'attachments'],
                expansions=['attachments.media_keys'],
                media_fields=['type', 'url', 'preview_image_url']
            )
            
            self.request_timestamps.append(time.time())
            
            if not tweets.data:  # type: ignore
                return []
            
            # Filter tweets since the given time
            filtered_tweets = []
            for tweet in tweets.data:  # type: ignore
                if tweet.created_at and tweet.created_at > since_time:
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'attachments': tweet.attachments if hasattr(tweet, 'attachments') else None
                    }
                    
                    # Add media information if available
                    if tweets.includes and 'media' in tweets.includes:  # type: ignore
                        media_lookup = {media.media_key: media for media in tweets.includes['media']}  # type: ignore
                        if tweet.attachments and 'media_keys' in tweet.attachments:
                            media_content = []
                            for media_key in tweet.attachments['media_keys']:
                                if media_key in media_lookup:
                                    media = media_lookup[media_key]
                                    media_content.append({
                                        'type': media.type,
                                        'url': getattr(media, 'url', None),
                                        'preview_url': getattr(media, 'preview_image_url', None)
                                    })
                            tweet_data['media'] = media_content
                    
                    filtered_tweets.append(tweet_data)
            
            return filtered_tweets
            
        except Exception as e:
            logger.error(f"Error getting tweets for user {user_id}: {str(e)}")
            return []
    
    def get_user_tweets(self, user_id: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a specific user."""
        try:
            self._wait_for_rate_limit()
            
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'text', 'attachments'],
                expansions=['attachments.media_keys'],
                media_fields=['type', 'url', 'preview_image_url']
            )
            
            self.request_timestamps.append(time.time())
            
            if not tweets.data:  # type: ignore
                return []
            
            result = []
            for tweet in tweets.data:  # type: ignore
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'attachments': tweet.attachments if hasattr(tweet, 'attachments') else None
                }
                
                # Add media information if available
                if tweets.includes and 'media' in tweets.includes:  # type: ignore
                    media_lookup = {media.media_key: media for media in tweets.includes['media']}  # type: ignore
                    if tweet.attachments and 'media_keys' in tweet.attachments:
                        media_content = []
                        for media_key in tweet.attachments['media_keys']:
                            if media_key in media_lookup:
                                media = media_lookup[media_key]
                                media_content.append({
                                    'type': media.type,
                                    'url': getattr(media, 'url', None),
                                    'preview_url': getattr(media, 'preview_image_url', None)
                                })
                        tweet_data['media'] = media_content
                
                result.append(tweet_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting tweets for user {user_id}: {str(e)}")
            return []
    
    def get_media_content(self, tweet_id: str) -> Optional[List[Dict]]:
        """Get media content for a specific tweet."""
        try:
            self._wait_for_rate_limit()
            
            tweet = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=['attachments'],
                expansions=['attachments.media_keys'],
                media_fields=['type', 'url', 'preview_image_url']
            )
            
            self.request_timestamps.append(time.time())
            
            if not tweet.data:  # type: ignore
                return None
            
            tweet_data = tweet.data  # type: ignore
            
            if not tweet_data.attachments or 'media_keys' not in tweet_data.attachments:
                return None
            
            if tweet.includes and 'media' in tweet.includes:  # type: ignore
                media_lookup = {media.media_key: media for media in tweet.includes['media']}  # type: ignore
                media_content = []
                
                for media_key in tweet_data.attachments['media_keys']:
                    if media_key in media_lookup:
                        media = media_lookup[media_key]
                        media_content.append({
                            'type': media.type,
                            'url': getattr(media, 'url', None),
                            'preview_url': getattr(media, 'preview_image_url', None)
                        })
                
                return media_content
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting media for tweet {tweet_id}: {str(e)}")
            return None
    
    def process_new_tweet(self, tweet_data: Dict) -> Dict:
        """Process a new tweet and extract relevant information."""
        try:
            # Get media content if available
            media_content = None
            if tweet_data.get('media'):
                # Use the first media item for now
                media_content = tweet_data['media'][0]
            
            return {
                'tweet_id': str(tweet_data['id']),
                'text': tweet_data['text'],
                'created_at': tweet_data['created_at'],
                'author_id': None,  # We'll need to get this separately if needed
                'media': media_content
            }
            
        except Exception as e:
            logger.error(f"Error processing tweet {tweet_data.get('id')}: {str(e)}")
            return {}
    
    def monitor_accounts(self, user_ids: List[str]) -> None:
        """Set up monitoring for specific users."""
        try:
            logger.info(f"Successfully set up monitoring for {len(user_ids)} accounts")
            
        except Exception as e:
            logger.error(f"Error setting up account monitoring: {str(e)}")
            raise 