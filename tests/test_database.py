"""Test database functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from sentiment_monitor.storage.database import DatabaseManager
from sentiment_monitor.storage.models import Keyword, Platform, Post, SentimentScore, Alert


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    def test_init_db(self, test_db):
        """Test database initialization."""
        assert test_db is not None
        
        # Check that tables exist
        with test_db.get_session() as session:
            # Should have default platforms
            platforms = session.query(Platform).all()
            platform_names = {p.name for p in platforms}
            
            expected_platforms = {'reddit', 'hackernews', 'twitter', 'news'}
            assert expected_platforms.issubset(platform_names)
    
    def test_add_keyword(self, test_db):
        """Test adding keywords."""
        keyword = test_db.add_keyword("test_keyword")
        
        assert keyword is not None
        assert keyword.keyword == "test_keyword"
        assert keyword.is_active is True
        
        # Test duplicate keyword
        keyword2 = test_db.add_keyword("test_keyword")
        assert keyword2.id == keyword.id  # Should return same keyword
    
    def test_remove_keyword(self, test_db):
        """Test removing keywords."""
        # Add keyword first
        test_db.add_keyword("test_keyword")
        
        # Remove it
        success = test_db.remove_keyword("test_keyword")
        assert success is True
        
        # Check it's deactivated
        with test_db.get_session() as session:
            keyword = session.query(Keyword).filter_by(keyword="test_keyword").first()
            assert keyword.is_active is False
        
        # Test removing non-existent keyword
        success = test_db.remove_keyword("non_existent")
        assert success is False
    
    def test_get_active_keywords(self, test_db):
        """Test getting active keywords."""
        # Add some keywords
        test_db.add_keyword("keyword1")
        test_db.add_keyword("keyword2")
        test_db.add_keyword("keyword3")
        
        # Remove one
        test_db.remove_keyword("keyword2")
        
        # Get active keywords
        active_keywords = test_db.get_active_keywords()
        keyword_names = {k.keyword for k in active_keywords}
        
        assert "keyword1" in keyword_names
        assert "keyword2" not in keyword_names
        assert "keyword3" in keyword_names
    
    def test_get_platform_by_name(self, test_db):
        """Test getting platform by name."""
        platform = test_db.get_platform_by_name("reddit")
        assert platform is not None
        assert platform.name == "reddit"
        
        # Test non-existent platform
        platform = test_db.get_platform_by_name("non_existent")
        assert platform is None
    
    def test_add_post(self, test_db, sample_posts):
        """Test adding posts."""
        # Setup keyword and platform
        keyword = test_db.add_keyword("test_keyword")
        platform = test_db.get_platform_by_name("reddit")
        
        # Update sample post data
        post_data = sample_posts[0].copy()
        post_data['keyword_id'] = keyword.id
        post_data['platform_id'] = platform.id
        
        # Add post
        post = test_db.add_post(post_data)
        assert post is not None
        assert post.external_id == "test_post_1"
        assert post.title == "Great news about test keyword"
        
        # Test duplicate post
        duplicate_post = test_db.add_post(post_data)
        assert duplicate_post is None  # Should skip duplicate
    
    def test_add_sentiment_score(self, test_db, sample_posts):
        """Test adding sentiment scores."""
        # Setup
        keyword = test_db.add_keyword("test_keyword")
        platform = test_db.get_platform_by_name("reddit")
        
        post_data = sample_posts[0].copy()
        post_data['keyword_id'] = keyword.id
        post_data['platform_id'] = platform.id
        
        post = test_db.add_post(post_data)
        
        # Add sentiment score
        score_data = {
            'post_id': post.id,
            'model_name': 'vader',
            'model_version': '3.3.2',
            'compound_score': 0.5,
            'positive_score': 0.7,
            'negative_score': 0.1,
            'neutral_score': 0.2,
            'confidence': 0.8,
            'processing_time': 0.1,
            'raw_output': {'compound': 0.5}
        }
        
        score = test_db.add_sentiment_score(score_data)
        assert score is not None
        assert score.compound_score == 0.5
        assert score.model_name == 'vader'
        
        # Test updating existing score
        score_data['compound_score'] = 0.6
        updated_score = test_db.add_sentiment_score(score_data)
        assert updated_score.compound_score == 0.6
    
    def test_get_recent_posts(self, test_db, sample_posts):
        """Test getting recent posts."""
        # Setup
        keyword = test_db.add_keyword("test_keyword")
        platform = test_db.get_platform_by_name("reddit")
        
        # Add posts
        for post_data in sample_posts:
            post_data['keyword_id'] = keyword.id
            post_data['platform_id'] = platform.id
            post_data['is_processed'] = True
            test_db.add_post(post_data)
        
        # Get recent posts
        recent_posts = test_db.get_recent_posts("test_keyword", hours=24, limit=10)
        
        assert len(recent_posts) == 3
        # Should be ordered by posted_at desc
        assert recent_posts[0].posted_at >= recent_posts[1].posted_at
    
    def test_get_sentiment_summary(self, test_db, sample_posts):
        """Test getting sentiment summary."""
        # Setup
        keyword = test_db.add_keyword("test_keyword")
        platform = test_db.get_platform_by_name("reddit")
        
        # Add posts with sentiment scores
        sentiment_scores = [0.8, -0.6, 0.1]  # positive, negative, neutral
        
        for i, post_data in enumerate(sample_posts):
            post_data['keyword_id'] = keyword.id
            post_data['platform_id'] = platform.id
            post = test_db.add_post(post_data)
            
            score_data = {
                'post_id': post.id,
                'model_name': 'vader',
                'compound_score': sentiment_scores[i],
                'positive_score': max(0, sentiment_scores[i]),
                'negative_score': max(0, -sentiment_scores[i]),
                'neutral_score': 1 - abs(sentiment_scores[i]),
                'confidence': 0.8
            }
            test_db.add_sentiment_score(score_data)
        
        # Get summary
        summary = test_db.get_sentiment_summary("test_keyword", hours=24)
        
        assert summary['total_posts'] == 3
        assert abs(summary['avg_sentiment'] - (0.8 - 0.6 + 0.1) / 3) < 0.01
        assert summary['positive_count'] >= 1
        assert summary['negative_count'] >= 1
    
    def test_add_alert(self, test_db):
        """Test adding alerts."""
        keyword = test_db.add_keyword("test_keyword")
        
        alert_data = {
            'keyword_id': keyword.id,
            'alert_type': 'sentiment_threshold',
            'severity': 'high',
            'message': 'Test alert message',
            'current_value': -0.8,
            'threshold_value': -0.5,
            'metadata': {'test': 'data'}
        }
        
        alert = test_db.add_alert(alert_data)
        assert alert is not None
        assert alert.message == 'Test alert message'
        assert alert.severity == 'high'
        assert alert.is_active is True
        assert alert.is_acknowledged is False
    
    def test_get_active_alerts(self, test_db):
        """Test getting active alerts."""
        keyword = test_db.add_keyword("test_keyword")
        
        # Add some alerts
        for i in range(3):
            alert_data = {
                'keyword_id': keyword.id,
                'alert_type': 'test',
                'severity': 'medium',
                'message': f'Test alert {i}',
                'current_value': 0.5,
                'threshold_value': 0.3
            }
            test_db.add_alert(alert_data)
        
        active_alerts = test_db.get_active_alerts()
        assert len(active_alerts) == 3
    
    def test_cleanup_old_data(self, test_db, sample_posts):
        """Test cleaning up old data."""
        # Setup
        keyword = test_db.add_keyword("test_keyword")
        platform = test_db.get_platform_by_name("reddit")
        
        # Add old post
        old_post_data = sample_posts[0].copy()
        old_post_data['keyword_id'] = keyword.id
        old_post_data['platform_id'] = platform.id
        old_post_data['collected_at'] = datetime.utcnow() - timedelta(days=10)
        old_post_data['external_id'] = 'old_post'
        
        test_db.add_post(old_post_data)
        
        # Add recent post
        recent_post_data = sample_posts[1].copy()
        recent_post_data['keyword_id'] = keyword.id
        recent_post_data['platform_id'] = platform.id
        recent_post_data['external_id'] = 'recent_post'
        
        test_db.add_post(recent_post_data)
        
        # Cleanup with 5 day retention
        test_db.cleanup_old_data(retention_days=5)
        
        # Check that old post is gone but recent post remains
        with test_db.get_session() as session:
            posts = session.query(Post).all()
            external_ids = {p.external_id for p in posts}
            
            assert 'old_post' not in external_ids
            assert 'recent_post' in external_ids
    
    def test_get_database_stats(self, test_db):
        """Test getting database statistics."""
        # Add some data
        keyword = test_db.add_keyword("test_keyword")
        
        stats = test_db.get_database_stats()
        
        assert 'total_keywords' in stats
        assert 'total_posts' in stats
        assert 'total_sentiment_scores' in stats
        assert 'active_alerts' in stats
        assert 'database_size_mb' in stats
        
        assert stats['total_keywords'] >= 1  # At least our test keyword