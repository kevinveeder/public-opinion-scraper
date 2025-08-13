"""Reddit data collector using PRAW."""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Iterator
import praw
from praw.exceptions import PRAWException
import requests.exceptions

from ..storage.database import get_db
from ..storage.models import Post, Keyword, Platform
from ..utils.config import get_config, get_secrets

logger = logging.getLogger(__name__)


class RedditCollector:
    """Collects posts and comments from Reddit using PRAW."""
    
    def __init__(self):
        self.config = get_config()
        self.secrets = get_secrets()
        self.db = get_db()
        self.reddit = None
        self._reddit_platform_id = None
        
        self._initialize_reddit()
    
    def _initialize_reddit(self) -> None:
        """Initialize Reddit API connection."""
        try:
            reddit_config = self.secrets.get('reddit', {})
            
            if not reddit_config.get('client_id') or not reddit_config.get('client_secret'):
                logger.error("Reddit API credentials not found. Please set up config/secrets.yaml")
                return
            
            self.reddit = praw.Reddit(
                client_id=reddit_config['client_id'],
                client_secret=reddit_config['client_secret'],
                user_agent=reddit_config.get('user_agent', 'SentimentMonitor/1.0 by Kevin Veeder'),
                username=reddit_config.get('username'),
                password=reddit_config.get('password')
            )
            
            # Test connection
            try:
                self.reddit.user.me()
                logger.info("Reddit API connection established (authenticated)")
            except:
                logger.info("Reddit API connection established (read-only)")
            
            # Get platform ID
            with self.db.get_session() as session:
                platform = session.query(Platform).filter_by(name='reddit').first()
                if platform:
                    self._reddit_platform_id = platform.id
                else:
                    logger.error("Reddit platform not found in database")
                    
        except Exception as e:
            logger.error(f"Error initializing Reddit API: {e}")
            self.reddit = None
    
    def is_available(self) -> bool:
        """Check if Reddit collector is available."""
        return self.reddit is not None and self._reddit_platform_id is not None
    
    def collect_posts_for_keyword(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Collect posts for a specific keyword."""
        if not self.is_available():
            logger.warning("Reddit collector not available")
            return []
        
        posts = []
        try:
            # Get keyword object from database
            with self.db.get_session() as session:
                keyword_obj = session.query(Keyword).filter_by(keyword=keyword).first()
                if not keyword_obj:
                    logger.warning(f"Keyword '{keyword}' not found in database")
                    return []
                keyword_id = keyword_obj.id
            
            # Search for posts containing the keyword
            subreddits = self.config.collection.platforms.get('reddit', {}).get('subreddits', ['all'])
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search in different time periods and sort methods
                    search_methods = [
                        ('new', subreddit.search(keyword, sort='new', time_filter='day', limit=limit//4)),
                        ('hot', subreddit.search(keyword, sort='relevance', time_filter='day', limit=limit//4)),
                        ('top', subreddit.search(keyword, sort='top', time_filter='week', limit=limit//4))
                    ]
                    
                    for method_name, search_results in search_methods:
                        collected_count = 0
                        for submission in search_results:
                            if collected_count >= limit // len(subreddits) // len(search_methods):
                                break
                                
                            try:
                                post_data = self._extract_post_data(submission, keyword_id)
                                if post_data and self._is_relevant_post(post_data, keyword):
                                    posts.append(post_data)
                                    collected_count += 1
                                    
                                    # Also collect top comments
                                    comment_posts = self._collect_comments(submission, keyword, keyword_id, max_comments=5)
                                    posts.extend(comment_posts)
                                    
                            except Exception as e:
                                logger.warning(f"Error processing submission {submission.id}: {e}")
                                continue
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Error searching subreddit {subreddit_name}: {e}")
                    continue
            
            logger.info(f"Collected {len(posts)} posts for keyword '{keyword}' from Reddit")
            
        except PRAWException as e:
            logger.error(f"Reddit API error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while collecting Reddit posts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error collecting Reddit posts: {e}")
        
        return posts
    
    def _extract_post_data(self, submission, keyword_id: int) -> Optional[Dict[str, Any]]:
        """Extract post data from Reddit submission."""
        try:
            # Skip deleted or removed posts
            if submission.selftext == '[deleted]' or submission.selftext == '[removed]':
                return None
            
            # Combine title and content
            content = submission.title
            if submission.selftext:
                content += f"\n\n{submission.selftext}"
            
            # Skip if content is too short
            if len(content.strip()) < 10:
                return None
            
            post_data = {
                'external_id': submission.id,
                'platform_id': self._reddit_platform_id,
                'keyword_id': keyword_id,
                'title': submission.title,
                'content': content,
                'url': submission.url if submission.url != submission.permalink else f"https://reddit.com{submission.permalink}",
                'author': str(submission.author) if submission.author else '[deleted]',
                'posted_at': datetime.fromtimestamp(submission.created_utc),
                'score': submission.score,
                'comment_count': submission.num_comments,
                'metadata': {
                    'subreddit': str(submission.subreddit),
                    'permalink': submission.permalink,
                    'is_self': submission.is_self,
                    'over_18': submission.over_18,
                    'upvote_ratio': getattr(submission, 'upvote_ratio', None),
                    'gilded': submission.gilded,
                    'archived': submission.archived,
                    'locked': submission.locked
                }
            }
            
            return post_data
            
        except Exception as e:
            logger.warning(f"Error extracting post data: {e}")
            return None
    
    def _collect_comments(self, submission, keyword: str, keyword_id: int, max_comments: int = 5) -> List[Dict[str, Any]]:
        """Collect relevant comments from a submission."""
        comments = []
        try:
            submission.comments.replace_more(limit=0)  # Don't expand "more comments"
            
            comment_count = 0
            for comment in submission.comments.list()[:max_comments * 2]:  # Get extra to filter
                if comment_count >= max_comments:
                    break
                
                try:
                    # Skip deleted comments or very short ones
                    if not hasattr(comment, 'body') or comment.body in ['[deleted]', '[removed]']:
                        continue
                    
                    if len(comment.body.strip()) < 20:
                        continue
                    
                    # Check if comment is relevant to keyword
                    if not self._contains_keyword(comment.body, keyword):
                        continue
                    
                    comment_data = {
                        'external_id': f"{submission.id}_{comment.id}",
                        'platform_id': self._reddit_platform_id,
                        'keyword_id': keyword_id,
                        'title': f"Comment on: {submission.title}",
                        'content': comment.body,
                        'url': f"https://reddit.com{comment.permalink}",
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'posted_at': datetime.fromtimestamp(comment.created_utc),
                        'score': comment.score,
                        'comment_count': 0,  # Comments don't have sub-comments in our model
                        'metadata': {
                            'subreddit': str(submission.subreddit),
                            'parent_id': submission.id,
                            'permalink': comment.permalink,
                            'is_comment': True,
                            'gilded': comment.gilded,
                            'archived': comment.archived
                        }
                    }
                    
                    comments.append(comment_data)
                    comment_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing comment: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error collecting comments: {e}")
        
        return comments
    
    def _is_relevant_post(self, post_data: Dict[str, Any], keyword: str) -> bool:
        """Check if post is relevant to the keyword."""
        text = f"{post_data.get('title', '')} {post_data.get('content', '')}"
        return self._contains_keyword(text, keyword)
    
    def _contains_keyword(self, text: str, keyword: str) -> bool:
        """Check if text contains the keyword (case-insensitive)."""
        if not text or not keyword:
            return False
        
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        # Simple keyword matching - can be enhanced with boolean operators later
        return keyword_lower in text_lower
    
    def collect_trending_topics(self, subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """Collect trending topics from specified subreddits."""
        if not self.is_available():
            return []
        
        if subreddits is None:
            subreddits = ['all', 'news', 'worldnews', 'technology']
        
        trending_posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts
                for submission in subreddit.hot(limit=10):
                    try:
                        trending_posts.append({
                            'title': submission.title,
                            'score': submission.score,
                            'subreddit': str(submission.subreddit),
                            'created': datetime.fromtimestamp(submission.created_utc),
                            'url': f"https://reddit.com{submission.permalink}",
                            'comment_count': submission.num_comments
                        })
                    except Exception as e:
                        logger.warning(f"Error processing trending submission: {e}")
                        continue
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Error getting trending from {subreddit_name}: {e}")
                continue
        
        return trending_posts
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Reddit API connection and return status."""
        status = {
            'available': False,
            'authenticated': False,
            'error': None,
            'rate_limit_remaining': None,
            'rate_limit_reset': None
        }
        
        try:
            if not self.reddit:
                status['error'] = "Reddit API not initialized"
                return status
            
            # Test basic connection
            subreddit = self.reddit.subreddit('test')
            list(subreddit.hot(limit=1))
            status['available'] = True
            
            # Test authentication
            try:
                user = self.reddit.user.me()
                if user:
                    status['authenticated'] = True
            except:
                pass  # Read-only access is fine
            
            # Get rate limit info if available
            try:
                status['rate_limit_remaining'] = self.reddit.auth.limits.get('remaining')
                status['rate_limit_reset'] = self.reddit.auth.limits.get('reset_timestamp')
            except:
                pass
            
        except Exception as e:
            status['error'] = str(e)
        
        return status