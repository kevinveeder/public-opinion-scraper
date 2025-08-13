"""Base collector interface and common functionality."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the collector is available and properly configured."""
        pass
    
    @abstractmethod
    def collect_posts_for_keyword(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Collect posts for a specific keyword."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the data source."""
        pass
    
    def validate_post_data(self, post_data: Dict[str, Any]) -> bool:
        """Validate that post data contains required fields."""
        required_fields = [
            'external_id', 'platform_id', 'keyword_id', 
            'content', 'posted_at'
        ]
        
        for field in required_fields:
            if field not in post_data:
                self.logger.warning(f"Missing required field '{field}' in post data")
                return False
        
        # Validate data types
        if not isinstance(post_data['posted_at'], datetime):
            self.logger.warning("posted_at must be a datetime object")
            return False
        
        if len(post_data['content'].strip()) < 5:
            self.logger.warning("Content too short")
            return False
        
        return True
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()
    
    def extract_metadata(self, raw_data: Any) -> Dict[str, Any]:
        """Extract metadata from raw platform data."""
        return {}
    
    def get_rate_limit_delay(self) -> float:
        """Get the delay needed for rate limiting."""
        return 1.0  # Default 1 second delay
    
    def handle_rate_limit(self, retry_after: Optional[float] = None) -> None:
        """Handle rate limiting by waiting appropriate time."""
        import time
        
        delay = retry_after if retry_after else self.get_rate_limit_delay()
        self.logger.info(f"Rate limited, waiting {delay} seconds")
        time.sleep(delay)
    
    def filter_duplicates(self, posts: List[Dict[str, Any]], 
                         existing_ids: set) -> List[Dict[str, Any]]:
        """Filter out duplicate posts based on external_id."""
        filtered_posts = []
        
        for post in posts:
            external_id = post.get('external_id')
            if external_id and external_id not in existing_ids:
                filtered_posts.append(post)
                existing_ids.add(external_id)
        
        return filtered_posts