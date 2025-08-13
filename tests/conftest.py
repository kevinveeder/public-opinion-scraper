"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src to path
import sys
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from sentiment_monitor.storage.database import DatabaseManager
from sentiment_monitor.storage.models import Base, Keyword, Platform, Post, SentimentScore
from sentiment_monitor.utils.config import ConfigManager
from sentiment_monitor.analysis.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    return {
        'database': {
            'path': ':memory:',  # Use in-memory database for tests
            'backup_interval_hours': 24,
            'retention_days': 7
        },
        'collection': {
            'polling_interval': 5,
            'max_posts_per_poll': 10,
            'platforms': {
                'reddit': {'enabled': True, 'subreddits': ['test']},
                'hackernews': {'enabled': True}
            }
        },
        'sentiment': {
            'models': {
                'vader': {'enabled': True, 'weight': 0.5},
                'roberta': {'enabled': False, 'weight': 0.5}  # Disable for tests
            },
            'confidence_threshold': 0.5
        },
        'keywords': {
            'default': ['test_keyword'],
            'boolean_support': True,
            'case_sensitive': False
        },
        'alerts': {
            'enabled': True,
            'thresholds': {
                'very_negative': -0.8,
                'negative': -0.3,
                'positive': 0.3,
                'very_positive': 0.8
            },
            'volume_threshold': 10,
            'rapid_change_threshold': 0.3
        },
        'dashboard': {
            'title': 'Test Sentiment Monitor',
            'refresh_interval_seconds': 30,
            'max_recent_posts': 10
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/test.log'
        },
        'performance': {
            'max_workers': 2,
            'request_timeout': 10,
            'max_retries': 2
        },
        'text_processing': {
            'max_text_length': 500,
            'detect_language': False,
            'target_language': 'en',
            'remove_urls': True,
            'remove_mentions': False,
            'remove_hashtags': False,
            'handle_emojis': True
        }
    }


@pytest.fixture
def test_db(test_config):
    """Create test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = DatabaseManager(db_path)
        yield db
    finally:
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.fixture
def sample_posts():
    """Create sample post data for testing."""
    return [
        {
            'external_id': 'test_post_1',
            'platform_id': 1,
            'keyword_id': 1,
            'title': 'Great news about test keyword',
            'content': 'This is a very positive post about the test keyword. Everything is amazing!',
            'url': 'https://example.com/post1',
            'author': 'test_user_1',
            'posted_at': datetime.utcnow() - timedelta(hours=1),
            'score': 100,
            'comment_count': 50,
            'metadata': {'platform': 'test', 'subreddit': 'test'}
        },
        {
            'external_id': 'test_post_2',
            'platform_id': 1,
            'keyword_id': 1,
            'title': 'Bad news about test keyword',
            'content': 'This is a negative post about the test keyword. Everything is terrible!',
            'url': 'https://example.com/post2',
            'author': 'test_user_2',
            'posted_at': datetime.utcnow() - timedelta(hours=2),
            'score': 10,
            'comment_count': 5,
            'metadata': {'platform': 'test', 'subreddit': 'test'}
        },
        {
            'external_id': 'test_post_3',
            'platform_id': 1,
            'keyword_id': 1,
            'title': 'Neutral post about test keyword',
            'content': 'This is a neutral post about the test keyword. Nothing special.',
            'url': 'https://example.com/post3',
            'author': 'test_user_3',
            'posted_at': datetime.utcnow() - timedelta(hours=3),
            'score': 25,
            'comment_count': 10,
            'metadata': {'platform': 'test', 'subreddit': 'test'}
        }
    ]


@pytest.fixture
def mock_reddit_submission():
    """Mock Reddit submission object."""
    submission = Mock()
    submission.id = 'test_submission'
    submission.title = 'Test Reddit Post'
    submission.selftext = 'This is a test post content'
    submission.url = 'https://reddit.com/r/test/comments/test'
    submission.author = Mock()
    submission.author.__str__ = Mock(return_value='test_author')
    submission.created_utc = datetime.utcnow().timestamp()
    submission.score = 100
    submission.num_comments = 50
    submission.subreddit = Mock()
    submission.subreddit.__str__ = Mock(return_value='test')
    submission.permalink = '/r/test/comments/test'
    submission.is_self = True
    submission.over_18 = False
    submission.upvote_ratio = 0.95
    submission.gilded = 0
    submission.archived = False
    submission.locked = False
    submission.comments = Mock()
    submission.comments.replace_more = Mock()
    submission.comments.list = Mock(return_value=[])
    return submission


@pytest.fixture
def mock_hn_story():
    """Mock Hacker News story object."""
    return {
        'id': 123456,
        'title': 'Test HN Story',
        'text': 'This is a test story content',
        'url': 'https://example.com/test',
        'by': 'test_author',
        'time': int(datetime.utcnow().timestamp()),
        'score': 100,
        'descendants': 50,
        'type': 'story',
        'kids': [123457, 123458]
    }


@pytest.fixture
def sentiment_analyzer():
    """Create sentiment analyzer for testing."""
    with patch('sentiment_monitor.analysis.sentiment_analyzer.HF_AVAILABLE', False):
        analyzer = SentimentAnalyzer()
    return analyzer


@pytest.fixture
def mock_requests_response():
    """Mock requests response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {'status': 'ok'}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, test_config):
    """Setup test environment for all tests."""
    # Mock configuration
    with patch('sentiment_monitor.utils.config.get_config') as mock_config:
        mock_config.return_value = Mock(**test_config)
        yield


def pytest_configure(config):
    """Configure pytest."""
    # Suppress warnings
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)