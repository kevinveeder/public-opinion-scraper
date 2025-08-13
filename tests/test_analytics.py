"""Test analytics and insights functionality."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from sentiment_monitor.analysis.analytics import (
    SentimentAnalytics, TrendAnalysis, AlertCondition
)


class TestSentimentAnalytics:
    """Test sentiment analytics functionality."""
    
    def setup_method(self):
        """Setup test data."""
        self.mock_trends_data = [
            {
                'timestamp': datetime.utcnow() - timedelta(hours=i),
                'sentiment': 0.1 + (i * 0.1),  # Increasing trend
                'confidence': 0.8,
                'model': 'vader'
            }
            for i in range(10, 0, -1)  # 10 data points
        ]
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_analyze_trends_increasing(self, mock_config, mock_db):
        """Test trend analysis with increasing sentiment."""
        # Setup mocks
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = self.mock_trends_data
        
        analytics = SentimentAnalytics()
        result = analytics.analyze_trends('test_keyword', hours=24)
        
        assert isinstance(result, TrendAnalysis)
        assert result.keyword == 'test_keyword'
        assert result.trend_direction == 'improving'
        assert result.trend_strength > 0
        assert result.sentiment_change > 0
        assert result.data_points == 10
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_analyze_trends_decreasing(self, mock_config, mock_db):
        """Test trend analysis with decreasing sentiment."""
        # Create decreasing trend data
        decreasing_trends = [
            {
                'timestamp': datetime.utcnow() - timedelta(hours=i),
                'sentiment': 1.0 - (i * 0.1),  # Decreasing trend
                'confidence': 0.8,
                'model': 'vader'
            }
            for i in range(10, 0, -1)
        ]
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = decreasing_trends
        
        analytics = SentimentAnalytics()
        result = analytics.analyze_trends('test_keyword', hours=24)
        
        assert result.trend_direction == 'declining'
        assert result.sentiment_change < 0
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_analyze_trends_insufficient_data(self, mock_config, mock_db):
        """Test trend analysis with insufficient data."""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = []  # No data
        
        analytics = SentimentAnalytics()
        result = analytics.analyze_trends('test_keyword', hours=24)
        
        assert result.trend_direction == 'insufficient_data'
        assert result.data_points == 0
        assert result.trend_strength == 0.0
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_calculate_momentum(self, mock_config, mock_db):
        """Test momentum calculation."""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = self.mock_trends_data
        
        analytics = SentimentAnalytics()
        result = analytics.calculate_momentum('test_keyword', hours=24)
        
        assert 'current_sentiment' in result
        assert 'sma_5' in result
        assert 'sma_10' in result
        assert 'momentum_signal' in result
        assert 'volatility' in result
        assert 'rate_of_change' in result
        assert result['momentum_signal'] in ['bullish', 'bearish', 'neutral']
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_calculate_momentum_insufficient_data(self, mock_config, mock_db):
        """Test momentum calculation with insufficient data."""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = self.mock_trends_data[:3]  # Only 3 points
        
        analytics = SentimentAnalytics()
        result = analytics.calculate_momentum('test_keyword', hours=24)
        
        assert 'error' in result
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_analyze_volume_correlation(self, mock_config, mock_db):
        """Test volume correlation analysis."""
        # Create data with volume variation
        trends_with_volume = []
        for i in range(20):
            trends_with_volume.extend([
                {
                    'timestamp': datetime.utcnow() - timedelta(hours=i) + timedelta(minutes=j*10),
                    'sentiment': 0.5 + np.random.normal(0, 0.1),
                    'confidence': 0.8,
                    'model': 'vader'
                }
                for j in range(np.random.randint(1, 6))  # Variable number of posts per hour
            ])
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = trends_with_volume
        
        analytics = SentimentAnalytics()
        result = analytics.analyze_volume_correlation('test_keyword', hours=24)
        
        assert 'correlation_coefficient' in result
        assert 'relationship_strength' in result
        assert 'volume_trend' in result
        assert 'avg_hourly_volume' in result
        assert result['relationship_strength'] in ['strong', 'moderate', 'weak']
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_detect_anomalies(self, mock_config, mock_db):
        """Test anomaly detection."""
        # Create data with anomalies
        normal_data = [
            {
                'timestamp': datetime.utcnow() - timedelta(hours=i),
                'sentiment': 0.1 + np.random.normal(0, 0.05),  # Normal variation
                'confidence': 0.8,
                'model': 'vader'
            }
            for i in range(25, 5, -1)
        ]
        
        # Add anomalies
        normal_data.extend([
            {
                'timestamp': datetime.utcnow() - timedelta(hours=4),
                'sentiment': 0.9,  # Positive spike
                'confidence': 0.8,
                'model': 'vader'
            },
            {
                'timestamp': datetime.utcnow() - timedelta(hours=3),
                'sentiment': -0.8,  # Negative spike
                'confidence': 0.8,
                'model': 'vader'
            }
        ])
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_trends.return_value = normal_data
        
        analytics = SentimentAnalytics()
        anomalies = analytics.detect_anomalies('test_keyword', hours=24)
        
        assert len(anomalies) >= 2  # Should detect both spikes
        
        # Check anomaly structure
        for anomaly in anomalies:
            assert 'timestamp' in anomaly
            assert 'sentiment' in anomaly
            assert 'z_score' in anomaly
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert anomaly['type'] in ['positive_spike', 'negative_spike']
            assert anomaly['severity'] in ['medium', 'high']
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_compare_keywords(self, mock_config, mock_db):
        """Test keyword comparison."""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        # Mock different summaries for different keywords
        def mock_get_sentiment_summary(keyword, hours):
            summaries = {
                'bitcoin': {
                    'avg_sentiment': 0.5,
                    'total_posts': 100,
                    'positive_count': 60,
                    'negative_count': 20,
                    'avg_confidence': 0.8
                },
                'ethereum': {
                    'avg_sentiment': -0.2,
                    'total_posts': 80,
                    'positive_count': 30,
                    'negative_count': 40,
                    'avg_confidence': 0.7
                }
            }
            return summaries.get(keyword, {})
        
        mock_db_instance.get_sentiment_summary.side_effect = mock_get_sentiment_summary
        
        # Mock trend analysis
        with patch.object(SentimentAnalytics, 'analyze_trends') as mock_analyze_trends:
            mock_analyze_trends.return_value = TrendAnalysis(
                keyword='test',
                period_hours=24,
                trend_direction='improving',
                trend_strength=0.8,
                sentiment_change=0.1,
                confidence_score=0.9,
                data_points=10,
                r_squared=0.7
            )
            
            analytics = SentimentAnalytics()
            result = analytics.compare_keywords(['bitcoin', 'ethereum'], hours=24)
            
            assert 'keyword_data' in result
            assert 'best_performing' in result
            assert 'worst_performing' in result
            assert 'most_discussed' in result
            
            assert result['best_performing'] == 'bitcoin'  # Higher sentiment
            assert result['worst_performing'] == 'ethereum'  # Lower sentiment
            assert result['most_discussed'] == 'bitcoin'  # More posts
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_check_alert_conditions(self, mock_config, mock_db):
        """Test alert condition checking."""
        # Setup config with alert thresholds
        mock_config_obj = Mock()
        mock_config_obj.alerts.enabled = True
        mock_config_obj.alerts.thresholds = {
            'very_negative': -0.8,
            'negative': -0.3,
            'positive': 0.3,
            'very_positive': 0.8
        }
        mock_config_obj.alerts.volume_threshold = 10
        mock_config_obj.alerts.rapid_change_threshold = 0.3
        mock_config.return_value = mock_config_obj
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        # Mock very negative sentiment
        mock_db_instance.get_sentiment_summary.return_value = {
            'avg_sentiment': -0.9,
            'total_posts': 15  # Above volume threshold
        }
        
        # Mock trend analysis for rapid change
        with patch.object(SentimentAnalytics, 'analyze_trends') as mock_analyze_trends:
            mock_analyze_trends.return_value = TrendAnalysis(
                keyword='test',
                period_hours=6,
                trend_direction='declining',
                trend_strength=0.8,
                sentiment_change=-0.4,  # Rapid negative change
                confidence_score=0.9,
                data_points=10,
                r_squared=0.7
            )
            
            analytics = SentimentAnalytics()
            alerts = analytics.check_alert_conditions('test_keyword')
            
            assert len(alerts) >= 2  # Should have sentiment and volume/change alerts
            
            # Check alert structure
            for alert in alerts:
                assert isinstance(alert, AlertCondition)
                assert alert.keyword == 'test_keyword'
                assert alert.triggered is True
                assert alert.alert_type in ['sentiment_threshold', 'volume_spike', 'rapid_change']
                assert alert.severity in ['low', 'medium', 'high', 'critical']
    
    @patch('sentiment_monitor.analysis.analytics.get_db')
    @patch('sentiment_monitor.analysis.analytics.get_config')
    def test_generate_insights(self, mock_config, mock_db):
        """Test comprehensive insights generation."""
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_sentiment_summary.return_value = {
            'avg_sentiment': 0.3,
            'total_posts': 50,
            'positive_count': 30,
            'negative_count': 10,
            'avg_confidence': 0.8
        }
        mock_db_instance.get_sentiment_trends.return_value = self.mock_trends_data
        
        mock_config_obj = Mock()
        mock_config_obj.alerts.enabled = True
        mock_config_obj.alerts.thresholds = {'negative': -0.3, 'positive': 0.3}
        mock_config_obj.alerts.volume_threshold = 10
        mock_config_obj.alerts.rapid_change_threshold = 0.3
        mock_config.return_value = mock_config_obj
        
        analytics = SentimentAnalytics()
        insights = analytics.generate_insights('test_keyword', hours=24)
        
        assert 'keyword' in insights
        assert 'summary' in insights
        assert 'trends' in insights
        assert 'momentum' in insights
        assert 'volume_correlation' in insights
        assert 'anomalies' in insights
        assert 'alerts' in insights
        assert 'recommendations' in insights
        
        assert insights['keyword'] == 'test_keyword'
        assert isinstance(insights['recommendations'], list)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        analytics = SentimentAnalytics()
        
        # Test with various insight scenarios
        insights = {
            'summary': {
                'total_posts': 5,  # Low volume
                'avg_sentiment': -0.6  # Negative sentiment
            },
            'trends': {
                'direction': 'declining',
                'confidence': 0.8  # High confidence
            },
            'momentum': {
                'momentum_signal': 'bearish',
                'volatility': 0.4  # High volatility
            },
            'alerts': [
                {'severity': 'critical', 'type': 'sentiment_threshold'}
            ],
            'anomalies': [
                {'type': 'negative_spike'},
                {'type': 'positive_spike'},
                {'type': 'negative_spike'}
            ]
        }
        
        recommendations = analytics._generate_recommendations(insights)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5  # Should limit to top 5
        
        # Check that recommendations address the issues
        rec_text = ' '.join(recommendations).lower()
        assert 'low' in rec_text or 'volume' in rec_text  # Should mention low volume
        assert 'negative' in rec_text or 'declining' in rec_text  # Should mention negative trend
        assert 'critical' in rec_text or 'immediate' in rec_text  # Should mention critical alerts