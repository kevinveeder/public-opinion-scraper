"""Hacker News data collector."""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from .base_collector import BaseCollector
from ..storage.database import get_db
from ..storage.models import Platform, Keyword
from ..utils.config import get_config

logger = logging.getLogger(__name__)


class HackerNewsCollector(BaseCollector):
    """Collects posts from Hacker News using their API and web scraping."""
    
    def __init__(self):
        super().__init__('hackernews')
        self.config = get_config()
        self.db = get_db()
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.web_url = "https://news.ycombinator.com"
        self._hn_platform_id = None
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Hacker News collector."""
        try:
            # Get platform ID
            with self.db.get_session() as session:
                platform = session.query(Platform).filter_by(name='hackernews').first()
                if platform:
                    self._hn_platform_id = platform.id
                else:
                    logger.error("Hacker News platform not found in database")
        except Exception as e:
            logger.error(f"Error initializing Hacker News collector: {e}")
    
    def is_available(self) -> bool:
        """Check if Hacker News collector is available."""
        return self._hn_platform_id is not None
    
    def collect_posts_for_keyword(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Collect posts from Hacker News for a specific keyword."""
        if not self.is_available():
            logger.warning("Hacker News collector not available")
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
            
            # Get top stories and new stories
            story_types = ['topstories', 'newstories']
            
            for story_type in story_types:
                try:
                    # Get story IDs
                    story_ids = self._get_story_ids(story_type, limit=limit*2)
                    
                    collected_count = 0
                    for story_id in story_ids:
                        if collected_count >= limit // len(story_types):
                            break
                        
                        try:
                            story_data = self._get_story_data(story_id)
                            if story_data and self._is_relevant_story(story_data, keyword):
                                post_data = self._convert_to_post_data(story_data, keyword_id)
                                if post_data:
                                    posts.append(post_data)
                                    collected_count += 1
                                    
                                    # Collect comments if the story is highly relevant
                                    if story_data.get('score', 0) > 50:
                                        comment_posts = self._collect_comments(story_data, keyword, keyword_id, max_comments=3)
                                        posts.extend(comment_posts)
                            
                        except Exception as e:
                            logger.warning(f"Error processing story {story_id}: {e}")
                            continue
                        
                        # Rate limiting
                        time.sleep(0.2)
                
                except Exception as e:
                    logger.warning(f"Error collecting {story_type}: {e}")
                    continue
            
            # Also search using Algolia HN Search API
            algolia_posts = self._search_algolia(keyword, keyword_id, limit=limit//4)
            posts.extend(algolia_posts)
            
            logger.info(f"Collected {len(posts)} posts for keyword '{keyword}' from Hacker News")
            
        except Exception as e:
            logger.error(f"Error collecting Hacker News posts: {e}")
        
        return posts
    
    def _get_story_ids(self, story_type: str, limit: int = 100) -> List[int]:
        """Get story IDs from Hacker News API."""
        try:
            response = requests.get(f"{self.base_url}/{story_type}.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:limit]
        except Exception as e:
            logger.error(f"Error getting {story_type} IDs: {e}")
            return []
    
    def _get_story_data(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get story data from Hacker News API."""
        try:
            response = requests.get(f"{self.base_url}/item/{story_id}.json", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Error getting story {story_id}: {e}")
            return None
    
    def _is_relevant_story(self, story_data: Dict[str, Any], keyword: str) -> bool:
        """Check if story is relevant to the keyword."""
        if not story_data or story_data.get('deleted') or story_data.get('dead'):
            return False
        
        title = story_data.get('title', '')
        text = story_data.get('text', '')
        url = story_data.get('url', '')
        
        search_text = f"{title} {text} {url}".lower()
        return keyword.lower() in search_text
    
    def _convert_to_post_data(self, story_data: Dict[str, Any], keyword_id: int) -> Optional[Dict[str, Any]]:
        """Convert HN story data to our post format."""
        try:
            story_id = story_data.get('id')
            if not story_id:
                return None
            
            title = story_data.get('title', '')
            text = story_data.get('text', '')
            content = title
            if text:
                content += f"\n\n{text}"
            
            # Skip if content is too short
            if len(content.strip()) < 10:
                return None
            
            post_data = {
                'external_id': str(story_id),
                'platform_id': self._hn_platform_id,
                'keyword_id': keyword_id,
                'title': title,
                'content': self.clean_text(content),
                'url': story_data.get('url', f"{self.web_url}/item?id={story_id}"),
                'author': story_data.get('by', 'anonymous'),
                'posted_at': datetime.fromtimestamp(story_data.get('time', 0)),
                'score': story_data.get('score', 0),
                'comment_count': story_data.get('descendants', 0),
                'metadata': {
                    'type': story_data.get('type', 'story'),
                    'hn_url': f"{self.web_url}/item?id={story_id}",
                    'kids': story_data.get('kids', []),
                    'parent': story_data.get('parent'),
                    'parts': story_data.get('parts', [])
                }
            }
            
            return post_data
            
        except Exception as e:
            logger.warning(f"Error converting story data: {e}")
            return None
    
    def _collect_comments(self, story_data: Dict[str, Any], keyword: str, 
                         keyword_id: int, max_comments: int = 3) -> List[Dict[str, Any]]:
        """Collect relevant comments from a story."""
        comments = []
        try:
            kids = story_data.get('kids', [])
            if not kids:
                return comments
            
            comment_count = 0
            for kid_id in kids[:max_comments * 2]:  # Get extra to filter
                if comment_count >= max_comments:
                    break
                
                try:
                    comment_data = self._get_story_data(kid_id)
                    if not comment_data or comment_data.get('deleted') or comment_data.get('dead'):
                        continue
                    
                    comment_text = comment_data.get('text', '')
                    if len(comment_text.strip()) < 20:
                        continue
                    
                    # Check if comment is relevant to keyword
                    if not self._contains_keyword(comment_text, keyword):
                        continue
                    
                    # Clean HTML from comment text
                    clean_text = self._clean_html(comment_text)
                    
                    comment_post = {
                        'external_id': f"{story_data['id']}_{kid_id}",
                        'platform_id': self._hn_platform_id,
                        'keyword_id': keyword_id,
                        'title': f"Comment on: {story_data.get('title', 'HN Story')}",
                        'content': clean_text,
                        'url': f"{self.web_url}/item?id={kid_id}",
                        'author': comment_data.get('by', 'anonymous'),
                        'posted_at': datetime.fromtimestamp(comment_data.get('time', 0)),
                        'score': 0,  # HN comments don't have scores in API
                        'comment_count': len(comment_data.get('kids', [])),
                        'metadata': {
                            'type': 'comment',
                            'parent_id': story_data['id'],
                            'hn_url': f"{self.web_url}/item?id={kid_id}",
                            'kids': comment_data.get('kids', [])
                        }
                    }
                    
                    comments.append(comment_post)
                    comment_count += 1
                    
                    time.sleep(0.1)  # Small delay between comment requests
                    
                except Exception as e:
                    logger.warning(f"Error processing comment {kid_id}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error collecting comments: {e}")
        
        return comments
    
    def _search_algolia(self, keyword: str, keyword_id: int, limit: int = 25) -> List[Dict[str, Any]]:
        """Search using Algolia HN Search API."""
        posts = []
        try:
            # Algolia HN Search endpoint
            search_url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': keyword,
                'tags': 'story',
                'hitsPerPage': limit,
                'page': 0
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for hit in data.get('hits', []):
                try:
                    if not hit.get('title') or not hit.get('objectID'):
                        continue
                    
                    post_data = {
                        'external_id': f"algolia_{hit['objectID']}",
                        'platform_id': self._hn_platform_id,
                        'keyword_id': keyword_id,
                        'title': hit.get('title', ''),
                        'content': hit.get('title', ''),  # Algolia doesn't provide story text
                        'url': hit.get('url', f"{self.web_url}/item?id={hit['objectID']}"),
                        'author': hit.get('author', 'anonymous'),
                        'posted_at': datetime.fromisoformat(hit.get('created_at', '').replace('Z', '+00:00')) if hit.get('created_at') else datetime.utcnow(),
                        'score': hit.get('points', 0),
                        'comment_count': hit.get('num_comments', 0),
                        'metadata': {
                            'type': 'story',
                            'hn_url': f"{self.web_url}/item?id={hit['objectID']}",
                            'algolia_search': True,
                            'tags': hit.get('_tags', [])
                        }
                    }
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing Algolia hit: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error searching Algolia: {e}")
        
        return posts
    
    def _contains_keyword(self, text: str, keyword: str) -> bool:
        """Check if text contains the keyword (case-insensitive)."""
        if not text or not keyword:
            return False
        return keyword.lower() in text.lower()
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags from text."""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            return soup.get_text()
        except:
            return html_text
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Hacker News API connection."""
        status = {
            'available': False,
            'error': None,
            'api_responsive': False,
            'algolia_responsive': False
        }
        
        try:
            # Test main API
            response = requests.get(f"{self.base_url}/topstories.json", timeout=10)
            if response.status_code == 200:
                status['api_responsive'] = True
            
            # Test Algolia search
            search_response = requests.get("https://hn.algolia.com/api/v1/search", 
                                         params={'query': 'test', 'hitsPerPage': 1}, timeout=10)
            if search_response.status_code == 200:
                status['algolia_responsive'] = True
            
            status['available'] = status['api_responsive'] or status['algolia_responsive']
            
        except Exception as e:
            status['error'] = str(e)
        
        return status