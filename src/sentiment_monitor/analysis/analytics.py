"""Advanced analytics and insights for sentiment data."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
from collections import defaultdict, Counter

from ..storage.database import get_db
from ..storage.models import Keyword, Post, SentimentScore, Alert
from ..utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Container for trend analysis results."""
    keyword: str
    period_hours: int
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1
    sentiment_change: float
    confidence_score: float
    data_points: int
    r_squared: float


@dataclass
class AlertCondition:
    """Container for alert condition results."""
    keyword: str
    alert_type: str
    severity: str
    message: str
    current_value: float
    threshold_value: float
    triggered: bool


class SentimentAnalytics:
    """Advanced sentiment analytics and insights."""
    
    def __init__(self):
        self.db = get_db()
        self.config = get_config()
    
    def analyze_trends(self, keyword: str, hours: int = 24) -> TrendAnalysis:
        """Analyze sentiment trends for a keyword."""
        try:
            trends = self.db.get_sentiment_trends(keyword, hours=hours)
            
            if len(trends) < 3:
                return TrendAnalysis(
                    keyword=keyword,
                    period_hours=hours,
                    trend_direction='insufficient_data',
                    trend_strength=0.0,
                    sentiment_change=0.0,
                    confidence_score=0.0,
                    data_points=len(trends),
                    r_squared=0.0
                )
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(trends)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate time-based features
            df['hours_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600
            
            # Linear regression for trend analysis
            x = df['hours_since_start'].values
            y = df['sentiment'].values
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Determine trend direction and strength
            trend_strength = abs(r_value)
            
            if abs(slope) < 0.001:  # Very small slope
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'improving'
            else:
                trend_direction = 'declining'
            
            # Calculate sentiment change
            sentiment_change = y[-1] - y[0] if len(y) > 0 else 0.0
            
            # Confidence based on R-squared and data points
            confidence_score = min(r_value ** 2 * (len(trends) / 10), 1.0)
            
            return TrendAnalysis(
                keyword=keyword,
                period_hours=hours,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                sentiment_change=sentiment_change,
                confidence_score=confidence_score,
                data_points=len(trends),
                r_squared=r_value ** 2
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trends for {keyword}: {e}")
            return TrendAnalysis(
                keyword=keyword,
                period_hours=hours,
                trend_direction='error',
                trend_strength=0.0,
                sentiment_change=0.0,
                confidence_score=0.0,
                data_points=0,
                r_squared=0.0
            )
    
    def calculate_momentum(self, keyword: str, hours: int = 24) -> Dict[str, Any]:
        """Calculate sentiment momentum indicators."""
        try:
            trends = self.db.get_sentiment_trends(keyword, hours=hours)
            
            if len(trends) < 5:
                return {'error': 'Insufficient data for momentum calculation'}
            
            df = pd.DataFrame(trends)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate moving averages
            df['sentiment_sma_5'] = df['sentiment'].rolling(window=5).mean()
            df['sentiment_sma_10'] = df['sentiment'].rolling(window=min(10, len(df))).mean()
            
            # Calculate momentum indicators
            current_sentiment = df['sentiment'].iloc[-1]
            sma_5 = df['sentiment_sma_5'].iloc[-1]
            sma_10 = df['sentiment_sma_10'].iloc[-1]
            
            # Momentum signal
            momentum_signal = 'bullish' if current_sentiment > sma_5 > sma_10 else 'bearish' if current_sentiment < sma_5 < sma_10 else 'neutral'
            
            # Volatility (standard deviation of recent sentiment)
            volatility = df['sentiment'].tail(10).std()
            
            # Rate of change
            roc_periods = min(5, len(df) - 1)
            rate_of_change = (current_sentiment - df['sentiment'].iloc[-roc_periods-1]) / roc_periods if roc_periods > 0 else 0
            
            return {
                'current_sentiment': current_sentiment,
                'sma_5': sma_5,
                'sma_10': sma_10,
                'momentum_signal': momentum_signal,
                'volatility': volatility,
                'rate_of_change': rate_of_change,
                'momentum_strength': abs(rate_of_change) * (1 - volatility) if volatility < 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum for {keyword}: {e}")
            return {'error': str(e)}
    
    def analyze_volume_correlation(self, keyword: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze correlation between volume and sentiment."""
        try:
            trends = self.db.get_sentiment_trends(keyword, hours=hours)
            
            if len(trends) < 10:
                return {'error': 'Insufficient data for correlation analysis'}
            
            df = pd.DataFrame(trends)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.floor('H')
            
            # Group by hour to get volume and average sentiment
            hourly_stats = df.groupby('hour').agg({
                'sentiment': ['mean', 'std', 'count'],
                'confidence': 'mean'
            }).round(4)
            
            hourly_stats.columns = ['avg_sentiment', 'sentiment_std', 'volume', 'avg_confidence']
            hourly_stats = hourly_stats.reset_index()
            
            # Calculate correlation
            correlation = hourly_stats['volume'].corr(hourly_stats['avg_sentiment'])
            
            # Determine relationship strength
            if abs(correlation) > 0.7:
                relationship = 'strong'
            elif abs(correlation) > 0.3:
                relationship = 'moderate'
            else:
                relationship = 'weak'
            
            # Volume trend analysis
            volume_trend = 'increasing' if hourly_stats['volume'].iloc[-1] > hourly_stats['volume'].iloc[0] else 'decreasing'
            
            return {
                'correlation_coefficient': correlation,
                'relationship_strength': relationship,
                'volume_trend': volume_trend,
                'peak_volume_hour': hourly_stats.loc[hourly_stats['volume'].idxmax(), 'hour'],
                'peak_sentiment_hour': hourly_stats.loc[hourly_stats['avg_sentiment'].idxmax(), 'hour'],
                'avg_hourly_volume': hourly_stats['volume'].mean(),
                'hourly_data': hourly_stats.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume correlation for {keyword}: {e}")
            return {'error': str(e)}
    
    def detect_anomalies(self, keyword: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect sentiment anomalies using statistical methods."""
        try:
            trends = self.db.get_sentiment_trends(keyword, hours=hours)
            
            if len(trends) < 20:
                return []
            
            df = pd.DataFrame(trends)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate rolling statistics
            window = min(10, len(df) // 2)
            df['rolling_mean'] = df['sentiment'].rolling(window=window).mean()
            df['rolling_std'] = df['sentiment'].rolling(window=window).std()
            
            # Z-score based anomaly detection
            df['z_score'] = (df['sentiment'] - df['rolling_mean']) / df['rolling_std']
            
            # Identify anomalies (z-score > 2 or < -2)
            anomalies = df[abs(df['z_score']) > 2].copy()
            
            anomaly_list = []
            for _, row in anomalies.iterrows():
                anomaly_type = 'positive_spike' if row['z_score'] > 0 else 'negative_spike'
                severity = 'high' if abs(row['z_score']) > 3 else 'medium'
                
                anomaly_list.append({
                    'timestamp': row['timestamp'],
                    'sentiment': row['sentiment'],
                    'z_score': row['z_score'],
                    'type': anomaly_type,
                    'severity': severity,
                    'deviation': abs(row['sentiment'] - row['rolling_mean'])
                })
            
            return anomaly_list
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {keyword}: {e}")
            return []
    
    def compare_keywords(self, keywords: List[str], hours: int = 24) -> Dict[str, Any]:
        """Compare sentiment across multiple keywords."""
        try:
            comparison_data = {}
            
            for keyword in keywords:
                summary = self.db.get_sentiment_summary(keyword, hours=hours)
                trends_analysis = self.analyze_trends(keyword, hours=hours)
                
                comparison_data[keyword] = {
                    'avg_sentiment': summary.get('avg_sentiment', 0),
                    'total_posts': summary.get('total_posts', 0),
                    'positive_ratio': summary.get('positive_count', 0) / max(summary.get('total_posts', 1), 1),
                    'negative_ratio': summary.get('negative_count', 0) / max(summary.get('total_posts', 1), 1),
                    'trend_direction': trends_analysis.trend_direction,
                    'trend_strength': trends_analysis.trend_strength,
                    'confidence': summary.get('avg_confidence', 0)
                }
            
            # Find best and worst performing keywords
            if comparison_data:
                best_keyword = max(comparison_data.keys(), key=lambda k: comparison_data[k]['avg_sentiment'])
                worst_keyword = min(comparison_data.keys(), key=lambda k: comparison_data[k]['avg_sentiment'])
                most_discussed = max(comparison_data.keys(), key=lambda k: comparison_data[k]['total_posts'])
                
                # Calculate correlation matrix
                sentiments = [data['avg_sentiment'] for data in comparison_data.values()]
                volumes = [data['total_posts'] for data in comparison_data.values()]
                
                return {
                    'keyword_data': comparison_data,
                    'best_performing': best_keyword,
                    'worst_performing': worst_keyword,
                    'most_discussed': most_discussed,
                    'sentiment_range': max(sentiments) - min(sentiments),
                    'volume_range': max(volumes) - min(volumes),
                    'average_sentiment': np.mean(sentiments),
                    'sentiment_std': np.std(sentiments)
                }
            else:
                return {'error': 'No data available for comparison'}
                
        except Exception as e:
            logger.error(f"Error comparing keywords: {e}")
            return {'error': str(e)}
    
    def check_alert_conditions(self, keyword: str) -> List[AlertCondition]:
        """Check if any alert conditions are met."""
        try:
            alerts = []
            config = self.config.alerts
            
            if not config.enabled:
                return alerts
            
            # Get recent data
            summary = self.db.get_sentiment_summary(keyword, hours=1)  # Last hour
            trend_analysis = self.analyze_trends(keyword, hours=6)  # 6 hour trend
            
            current_sentiment = summary.get('avg_sentiment', 0)
            volume = summary.get('total_posts', 0)
            
            # Sentiment threshold alerts
            thresholds = config.thresholds
            
            if current_sentiment <= thresholds.get('very_negative', -0.8):
                alerts.append(AlertCondition(
                    keyword=keyword,
                    alert_type='sentiment_threshold',
                    severity='critical',
                    message=f'Very negative sentiment detected: {current_sentiment:.3f}',
                    current_value=current_sentiment,
                    threshold_value=thresholds['very_negative'],
                    triggered=True
                ))
            elif current_sentiment <= thresholds.get('negative', -0.3):
                alerts.append(AlertCondition(
                    keyword=keyword,
                    alert_type='sentiment_threshold',
                    severity='high',
                    message=f'Negative sentiment detected: {current_sentiment:.3f}',
                    current_value=current_sentiment,
                    threshold_value=thresholds['negative'],
                    triggered=True
                ))
            elif current_sentiment >= thresholds.get('very_positive', 0.8):
                alerts.append(AlertCondition(
                    keyword=keyword,
                    alert_type='sentiment_threshold',
                    severity='low',
                    message=f'Very positive sentiment detected: {current_sentiment:.3f}',
                    current_value=current_sentiment,
                    threshold_value=thresholds['very_positive'],
                    triggered=True
                ))
            
            # Volume threshold alerts
            volume_threshold = config.volume_threshold
            if volume > volume_threshold:
                alerts.append(AlertCondition(
                    keyword=keyword,
                    alert_type='volume_spike',
                    severity='medium',
                    message=f'High volume detected: {volume} posts in last hour',
                    current_value=volume,
                    threshold_value=volume_threshold,
                    triggered=True
                ))
            
            # Rapid change alerts
            rapid_change_threshold = config.rapid_change_threshold
            if abs(trend_analysis.sentiment_change) > rapid_change_threshold:
                direction = 'improvement' if trend_analysis.sentiment_change > 0 else 'decline'
                alerts.append(AlertCondition(
                    keyword=keyword,
                    alert_type='rapid_change',
                    severity='medium',
                    message=f'Rapid sentiment {direction}: {trend_analysis.sentiment_change:.3f} change',
                    current_value=abs(trend_analysis.sentiment_change),
                    threshold_value=rapid_change_threshold,
                    triggered=True
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alert conditions for {keyword}: {e}")
            return []
    
    def generate_insights(self, keyword: str, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive insights for a keyword."""
        try:
            insights = {
                'keyword': keyword,
                'analysis_period': hours,
                'generated_at': datetime.utcnow(),
                'summary': {},
                'trends': {},
                'momentum': {},
                'volume_correlation': {},
                'anomalies': [],
                'alerts': [],
                'recommendations': []
            }
            
            # Basic summary
            summary = self.db.get_sentiment_summary(keyword, hours=hours)
            insights['summary'] = summary
            
            # Trend analysis
            trend_analysis = self.analyze_trends(keyword, hours=hours)
            insights['trends'] = {
                'direction': trend_analysis.trend_direction,
                'strength': trend_analysis.trend_strength,
                'change': trend_analysis.sentiment_change,
                'confidence': trend_analysis.confidence_score,
                'r_squared': trend_analysis.r_squared
            }
            
            # Momentum analysis
            insights['momentum'] = self.calculate_momentum(keyword, hours=hours)
            
            # Volume correlation
            insights['volume_correlation'] = self.analyze_volume_correlation(keyword, hours=hours)
            
            # Anomaly detection
            insights['anomalies'] = self.detect_anomalies(keyword, hours=hours)
            
            # Alert conditions
            alert_conditions = self.check_alert_conditions(keyword)
            insights['alerts'] = [
                {
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'triggered': alert.triggered
                }
                for alert in alert_conditions
            ]
            
            # Generate recommendations
            insights['recommendations'] = self._generate_recommendations(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for {keyword}: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on insights."""
        recommendations = []
        
        try:
            summary = insights.get('summary', {})
            trends = insights.get('trends', {})
            momentum = insights.get('momentum', {})
            alerts = insights.get('alerts', [])
            anomalies = insights.get('anomalies', [])
            
            # Volume-based recommendations
            total_posts = summary.get('total_posts', 0)
            if total_posts < 10:
                recommendations.append("Consider expanding data collection - low post volume detected")
            elif total_posts > 100:
                recommendations.append("High engagement detected - monitor for emerging trends")
            
            # Sentiment-based recommendations
            avg_sentiment = summary.get('avg_sentiment', 0)
            if avg_sentiment < -0.5:
                recommendations.append("Negative sentiment detected - investigate potential issues or crises")
            elif avg_sentiment > 0.5:
                recommendations.append("Positive sentiment detected - consider leveraging this momentum")
            
            # Trend-based recommendations
            trend_direction = trends.get('direction', 'stable')
            if trend_direction == 'declining' and trends.get('confidence', 0) > 0.7:
                recommendations.append("Strong declining trend - immediate attention recommended")
            elif trend_direction == 'improving' and trends.get('confidence', 0) > 0.7:
                recommendations.append("Strong positive trend - monitor for optimization opportunities")
            
            # Momentum-based recommendations
            momentum_signal = momentum.get('momentum_signal', 'neutral')
            if momentum_signal == 'bearish':
                recommendations.append("Bearish momentum - prepare for potential negative sentiment increase")
            elif momentum_signal == 'bullish':
                recommendations.append("Bullish momentum - positive sentiment trend likely to continue")
            
            # Alert-based recommendations
            critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
            if critical_alerts:
                recommendations.append("Critical alerts detected - immediate response required")
            
            # Anomaly-based recommendations
            if len(anomalies) > 2:
                recommendations.append("Multiple anomalies detected - investigate unusual activity")
            
            # Volatility recommendations
            volatility = momentum.get('volatility', 0)
            if volatility > 0.3:
                recommendations.append("High volatility detected - sentiment may be unstable")
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations - check system logs"]


# Global analytics instance
analytics = SentimentAnalytics()

def get_analytics() -> SentimentAnalytics:
    """Get the global analytics instance."""
    return analytics