"""Test data collection functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from sentiment_monitor.collectors.reddit_collector import RedditCollector
from sentiment_monitor.collectors.hackernews_collector import HackerNewsCollector
from sentiment_monitor.collectors.base_collector import BaseCollector


class TestBaseCollector:
    """Test base collector functionality."""
    
    def test_validate_post_data(self):
        """Test post data validation."""
        # Create a concrete implementation for testing
        class TestCollector(BaseCollector):
            def is_available(self):
                return True
            
            def collect_posts_for_keyword(self, keyword, limit=100):
                return []
            
            def test_connection(self):
                return {'available': True}
        
        collector = TestCollector("test")
        
        # Valid post data
        valid_post = {
            'external_id': 'test_123',
            'platform_id': 1,
            'keyword_id': 1,
            'content': 'This is a test post content',
            'posted_at': datetime.utcnow()
        }
        
        assert collector.validate_post_data(valid_post) is True
        
        # Missing required field
        invalid_post = valid_post.copy()
        del invalid_post['external_id']
        assert collector.validate_post_data(invalid_post) is False
        
        # Invalid content (too short)
        invalid_post = valid_post.copy()
        invalid_post['content'] = 'hi'
        assert collector.validate_post_data(invalid_post) is False
        
        # Invalid date type
        invalid_post = valid_post.copy()
        invalid_post['posted_at'] = 'not a date'
        assert collector.validate_post_data(invalid_post) is False
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        class TestCollector(BaseCollector):
            def is_available(self):
                return True
            
            def collect_posts_for_keyword(self, keyword, limit=100):
                return []
            
            def test_connection(self):
                return {'available': True}
        
        collector = TestCollector("test")
        
        # Test cleaning
        dirty_text = "  This   has   extra    spaces  \n\t  "
        clean_text = collector.clean_text(dirty_text)
        assert clean_text == "This has extra spaces"
        
        # Test empty text
        assert collector.clean_text("") == ""
        assert collector.clean_text(None) == ""
    
    def test_filter_duplicates(self):
        """Test duplicate filtering."""
        class TestCollector(BaseCollector):
            def is_available(self):
                return True
            
            def collect_posts_for_keyword(self, keyword, limit=100):
                return []
            
            def test_connection(self):
                return {'available': True}
        
        collector = TestCollector("test")
        
        posts = [
            {'external_id': 'post_1', 'content': 'Content 1'},
            {'external_id': 'post_2', 'content': 'Content 2'},
            {'external_id': 'post_1', 'content': 'Duplicate content'},  # Duplicate
            {'external_id': 'post_3', 'content': 'Content 3'}
        ]
        
        existing_ids = {'post_2'}  # post_2 already exists
        
        filtered = collector.filter_duplicates(posts, existing_ids)
        
        assert len(filtered) == 2  # Should have post_1 and post_3 only
        filtered_ids = {p['external_id'] for p in filtered}
        assert 'post_1' in filtered_ids
        assert 'post_3' in filtered_ids
        assert 'post_2' not in filtered_ids  # Was in existing_ids


class TestRedditCollector:
    """Test Reddit data collector."""
    
    @patch('sentiment_monitor.collectors.reddit_collector.praw')
    def test_initialization(self, mock_praw):
        """Test Reddit collector initialization."""
        # Mock PRAW Reddit instance
        mock_reddit = Mock()
        mock_praw.Reddit.return_value = mock_reddit
        
        with patch('sentiment_monitor.collectors.reddit_collector.get_secrets') as mock_secrets:
            mock_secrets.return_value = {
                'reddit': {
                    'client_id': 'test_id',
                    'client_secret': 'test_secret',
                    'user_agent': 'test_agent'
                }
            }
            
            collector = RedditCollector()
            
            assert collector.reddit is not None
            mock_praw.Reddit.assert_called_once()
    
    @patch('sentiment_monitor.collectors.reddit_collector.praw')
    def test_is_available(self, mock_praw):
        """Test availability check."""
        mock_reddit = Mock()
        mock_praw.Reddit.return_value = mock_reddit
        
        with patch('sentiment_monitor.collectors.reddit_collector.get_secrets') as mock_secrets:
            mock_secrets.return_value = {
                'reddit': {
                    'client_id': 'test_id',
                    'client_secret': 'test_secret'
                }
            }
            
            with patch('sentiment_monitor.collectors.reddit_collector.get_db') as mock_db:
                mock_db_instance = Mock()
                mock_db.return_value = mock_db_instance
                
                # Mock platform query
                mock_session = Mock()
                mock_platform = Mock()
                mock_platform.id = 1
                mock_session.query.return_value.filter_by.return_value.first.return_value = mock_platform
                mock_db_instance.get_session.return_value.__enter__.return_value = mock_session
                
                collector = RedditCollector()
                assert collector.is_available() is True
    
    def test_extract_post_data(self):
        """Test post data extraction from Reddit submission."""
        with patch('sentiment_monitor.collectors.reddit_collector.get_db') as mock_db, \
             patch('sentiment_monitor.collectors.reddit_collector.get_secrets') as mock_secrets, \
             patch('sentiment_monitor.collectors.reddit_collector.praw'):
            
            mock_secrets.return_value = {'reddit': {'client_id': 'test', 'client_secret': 'test'}}
            
            # Mock database
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            mock_session = Mock()
            mock_platform = Mock()
            mock_platform.id = 1
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_platform
            mock_db_instance.get_session.return_value.__enter__.return_value = mock_session
            
            collector = RedditCollector()
            collector._reddit_platform_id = 1
            
            # Mock submission
            submission = Mock()
            submission.id = 'test_123'
            submission.title = 'Test Post Title'
            submission.selftext = 'Test post content'
            submission.url = 'https://example.com'
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
            
            post_data = collector._extract_post_data(submission, keyword_id=1)
            
            assert post_data is not None
            assert post_data['external_id'] == 'test_123'
            assert post_data['title'] == 'Test Post Title'
            assert 'Test Post Title' in post_data['content']
            assert 'Test post content' in post_data['content']
            assert post_data['author'] == 'test_author'
            assert post_data['platform_id'] == 1
            assert post_data['keyword_id'] == 1
    
    def test_contains_keyword(self):
        """Test keyword matching."""
        with patch('sentiment_monitor.collectors.reddit_collector.get_db'), \
             patch('sentiment_monitor.collectors.reddit_collector.get_secrets') as mock_secrets, \
             patch('sentiment_monitor.collectors.reddit_collector.praw'):
            
            mock_secrets.return_value = {'reddit': {'client_id': 'test', 'client_secret': 'test'}}
            
            collector = RedditCollector()
            
            # Case insensitive matching
            assert collector._contains_keyword("This post mentions Bitcoin", "bitcoin") is True
            assert collector._contains_keyword("BITCOIN is trending", "bitcoin") is True
            assert collector._contains_keyword("This post is about Ethereum", "bitcoin") is False
            assert collector._contains_keyword("", "bitcoin") is False
            assert collector._contains_keyword("Some text", "") is False
    
    @patch('sentiment_monitor.collectors.reddit_collector.requests')
    def test_test_connection(self, mock_requests):
        """Test connection testing."""
        with patch('sentiment_monitor.collectors.reddit_collector.get_db'), \
             patch('sentiment_monitor.collectors.reddit_collector.get_secrets') as mock_secrets, \
             patch('sentiment_monitor.collectors.reddit_collector.praw') as mock_praw:
            
            mock_secrets.return_value = {'reddit': {'client_id': 'test', 'client_secret': 'test'}}
            
            # Mock successful Reddit connection
            mock_reddit = Mock()
            mock_subreddit = Mock()
            mock_subreddit.hot.return_value = [Mock()]
            mock_reddit.subreddit.return_value = mock_subreddit
            mock_praw.Reddit.return_value = mock_reddit
            
            collector = RedditCollector()
            status = collector.test_connection()
            
            assert 'available' in status
            assert 'authenticated' in status


class TestHackerNewsCollector:
    """Test Hacker News data collector."""
    
    def test_initialization(self):
        """Test HackerNews collector initialization."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db') as mock_db:
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            # Mock platform query
            mock_session = Mock()
            mock_platform = Mock()
            mock_platform.id = 2
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_platform
            mock_db_instance.get_session.return_value.__enter__.return_value = mock_session
            
            collector = HackerNewsCollector()
            assert collector._hn_platform_id == 2
    
    def test_is_available(self):
        """Test availability check."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db') as mock_db:
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            mock_session = Mock()
            mock_platform = Mock()
            mock_platform.id = 2
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_platform
            mock_db_instance.get_session.return_value.__enter__.return_value = mock_session
            
            collector = HackerNewsCollector()
            assert collector.is_available() is True
    
    @patch('sentiment_monitor.collectors.hackernews_collector.requests')
    def test_get_story_ids(self, mock_requests):
        """Test getting story IDs."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            # Mock successful API response
            mock_response = Mock()
            mock_response.json.return_value = [1, 2, 3, 4, 5]
            mock_response.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_response
            
            collector = HackerNewsCollector()
            story_ids = collector._get_story_ids('topstories', limit=3)
            
            assert story_ids == [1, 2, 3]
            mock_requests.get.assert_called_once()
    
    @patch('sentiment_monitor.collectors.hackernews_collector.requests')
    def test_get_story_data(self, mock_requests):
        """Test getting story data."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            # Mock successful API response
            mock_response = Mock()
            mock_response.json.return_value = {
                'id': 123,
                'title': 'Test HN Story',
                'text': 'Story content',
                'by': 'test_author',
                'time': 1640995200,  # 2022-01-01
                'score': 100,
                'descendants': 50
            }
            mock_response.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_response
            
            collector = HackerNewsCollector()
            story_data = collector._get_story_data(123)
            
            assert story_data is not None
            assert story_data['id'] == 123
            assert story_data['title'] == 'Test HN Story'
    
    def test_is_relevant_story(self):
        """Test story relevance checking."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            collector = HackerNewsCollector()
            
            # Relevant story
            relevant_story = {
                'title': 'Bitcoin reaches new heights',
                'text': 'The cryptocurrency market is booming',
                'url': 'https://example.com/bitcoin-news'
            }
            assert collector._is_relevant_story(relevant_story, 'bitcoin') is True
            
            # Irrelevant story
            irrelevant_story = {
                'title': 'New JavaScript framework released',
                'text': 'This framework makes development easier',
                'url': 'https://example.com/js-news'
            }
            assert collector._is_relevant_story(irrelevant_story, 'bitcoin') is False
            
            # Deleted/dead story
            deleted_story = {'deleted': True}
            assert collector._is_relevant_story(deleted_story, 'bitcoin') is False
    
    def test_convert_to_post_data(self):
        """Test converting HN story to post format."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            collector = HackerNewsCollector()
            collector._hn_platform_id = 2
            
            story_data = {
                'id': 123456,
                'title': 'Test HN Story Title',
                'text': 'Test story content',
                'url': 'https://example.com/story',
                'by': 'test_author',
                'time': 1640995200,
                'score': 100,
                'descendants': 50,
                'type': 'story'
            }
            
            post_data = collector._convert_to_post_data(story_data, keyword_id=1)
            
            assert post_data is not None
            assert post_data['external_id'] == '123456'
            assert post_data['title'] == 'Test HN Story Title'
            assert 'Test HN Story Title' in post_data['content']
            assert 'Test story content' in post_data['content']
            assert post_data['author'] == 'test_author'
            assert post_data['platform_id'] == 2
            assert post_data['keyword_id'] == 1
            assert post_data['score'] == 100
    
    @patch('sentiment_monitor.collectors.hackernews_collector.requests')
    def test_search_algolia(self, mock_requests):
        """Test Algolia search functionality."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            # Mock Algolia API response
            mock_response = Mock()
            mock_response.json.return_value = {
                'hits': [
                    {
                        'objectID': '789',
                        'title': 'Bitcoin Discussion',
                        'url': 'https://example.com',
                        'author': 'hn_user',
                        'created_at': '2022-01-01T00:00:00.000Z',
                        'points': 150,
                        'num_comments': 75,
                        '_tags': ['story']
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_response
            
            collector = HackerNewsCollector()
            collector._hn_platform_id = 2
            
            posts = collector._search_algolia('bitcoin', keyword_id=1, limit=10)
            
            assert len(posts) == 1
            assert posts[0]['external_id'] == 'algolia_789'
            assert posts[0]['title'] == 'Bitcoin Discussion'
    
    @patch('sentiment_monitor.collectors.hackernews_collector.requests')
    def test_test_connection(self, mock_requests):
        """Test connection testing."""
        with patch('sentiment_monitor.collectors.hackernews_collector.get_db'):
            # Mock successful API responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response
            
            collector = HackerNewsCollector()
            status = collector.test_connection()
            
            assert 'available' in status
            assert 'api_responsive' in status
            assert 'algolia_responsive' in status