"""Database management and operations."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Keyword, Platform, Post, SentimentScore, Alert, SentimentSummary
from ..utils.config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.config = get_config()
        self.db_path = db_path or self.config.database.path
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,  # Set to True for SQL debugging
            pool_recycle=3600,
            connect_args={'check_same_thread': False}
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize database
        self.init_db()
    
    def init_db(self) -> None:
        """Initialize database tables and default data."""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
            # Insert default platforms if they don't exist
            self._insert_default_platforms()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _insert_default_platforms(self) -> None:
        """Insert default social media platforms."""
        with self.get_session() as session:
            existing_platforms = session.query(Platform).all()
            existing_names = {p.name for p in existing_platforms}
            
            default_platforms = ['reddit', 'hackernews', 'twitter', 'news']
            
            for platform_name in default_platforms:
                if platform_name not in existing_names:
                    platform = Platform(name=platform_name)
                    session.add(platform)
            
            session.commit()
            logger.info("Default platforms initialized")
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def add_keyword(self, keyword: str) -> Keyword:
        """Add a new keyword to monitor."""
        with self.get_session() as session:
            # Check if keyword already exists
            existing = session.query(Keyword).filter_by(keyword=keyword).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.updated_at = datetime.utcnow()
                    session.commit()
                return existing
            
            # Create new keyword
            new_keyword = Keyword(keyword=keyword)
            session.add(new_keyword)
            session.commit()
            session.refresh(new_keyword)
            
            logger.info(f"Added new keyword: {keyword}")
            return new_keyword
    
    def remove_keyword(self, keyword: str) -> bool:
        """Deactivate a keyword (don't delete to preserve history)."""
        with self.get_session() as session:
            keyword_obj = session.query(Keyword).filter_by(keyword=keyword).first()
            if keyword_obj:
                keyword_obj.is_active = False
                keyword_obj.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Deactivated keyword: {keyword}")
                return True
            return False
    
    def get_active_keywords(self) -> List[Keyword]:
        """Get all active keywords."""
        with self.get_session() as session:
            return session.query(Keyword).filter_by(is_active=True).all()
    
    def get_platform_by_name(self, name: str) -> Optional[Platform]:
        """Get platform by name."""
        with self.get_session() as session:
            return session.query(Platform).filter_by(name=name).first()
    
    def add_post(self, post_data: Dict[str, Any]) -> Optional[Post]:
        """Add a new post to the database."""
        with self.get_session() as session:
            try:
                # Check for duplicates
                existing = session.query(Post).filter_by(
                    platform_id=post_data['platform_id'],
                    external_id=post_data['external_id']
                ).first()
                
                if existing:
                    return None  # Skip duplicate
                
                # Create new post
                post = Post(**post_data)
                session.add(post)
                session.commit()
                session.refresh(post)
                
                return post
                
            except SQLAlchemyError as e:
                logger.error(f"Error adding post: {e}")
                return None
    
    def add_sentiment_score(self, score_data: Dict[str, Any]) -> Optional[SentimentScore]:
        """Add sentiment score for a post."""
        with self.get_session() as session:
            try:
                # Check if score already exists for this post and model
                existing = session.query(SentimentScore).filter_by(
                    post_id=score_data['post_id'],
                    model_name=score_data['model_name']
                ).first()
                
                if existing:
                    # Update existing score
                    for key, value in score_data.items():
                        setattr(existing, key, value)
                    score = existing
                else:
                    # Create new score
                    score = SentimentScore(**score_data)
                    session.add(score)
                
                session.commit()
                session.refresh(score)
                return score
                
            except SQLAlchemyError as e:
                logger.error(f"Error adding sentiment score: {e}")
                return None
    
    def get_recent_posts(self, keyword: str, hours: int = 24, limit: int = 100) -> List[Post]:
        """Get recent posts for a keyword."""
        with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            return session.query(Post).join(Keyword).filter(
                and_(
                    Keyword.keyword == keyword,
                    Post.posted_at >= cutoff_time,
                    Post.is_processed == True
                )
            ).order_by(Post.posted_at.desc()).limit(limit).all()
    
    def get_sentiment_trends(self, keyword: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get sentiment trends for a keyword over time."""
        with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Query for sentiment scores with timestamps
            results = session.query(
                Post.posted_at,
                SentimentScore.compound_score,
                SentimentScore.confidence,
                SentimentScore.model_name
            ).join(SentimentScore).join(Keyword).filter(
                and_(
                    Keyword.keyword == keyword,
                    Post.posted_at >= cutoff_time,
                    SentimentScore.confidence >= 0.5  # Only high confidence scores
                )
            ).order_by(Post.posted_at).all()
            
            return [
                {
                    'timestamp': result.posted_at,
                    'sentiment': result.compound_score,
                    'confidence': result.confidence,
                    'model': result.model_name
                }
                for result in results
            ]
    
    def get_sentiment_summary(self, keyword: str, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated sentiment statistics for a keyword."""
        with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get basic stats
            stats = session.query(
                func.count(SentimentScore.id).label('total_posts'),
                func.avg(SentimentScore.compound_score).label('avg_sentiment'),
                func.avg(SentimentScore.confidence).label('avg_confidence'),
                func.count(func.nullif(SentimentScore.compound_score > 0.1, False)).label('positive_count'),
                func.count(func.nullif(SentimentScore.compound_score < -0.1, False)).label('negative_count'),
                func.count(func.nullif(and_(SentimentScore.compound_score >= -0.1, SentimentScore.compound_score <= 0.1), False)).label('neutral_count')
            ).join(Post).join(Keyword).filter(
                and_(
                    Keyword.keyword == keyword,
                    Post.posted_at >= cutoff_time
                )
            ).first()
            
            return {
                'total_posts': stats.total_posts or 0,
                'avg_sentiment': float(stats.avg_sentiment or 0),
                'avg_confidence': float(stats.avg_confidence or 0),
                'positive_count': stats.positive_count or 0,
                'negative_count': stats.negative_count or 0,
                'neutral_count': stats.neutral_count or 0,
                'period_hours': hours
            }
    
    def add_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Add a new alert."""
        with self.get_session() as session:
            alert = Alert(**alert_data)
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self.get_session() as session:
            return session.query(Alert).filter_by(is_active=True, is_acknowledged=False).all()
    
    def cleanup_old_data(self, retention_days: int = None) -> None:
        """Clean up old data based on retention policy."""
        if retention_days is None:
            retention_days = self.config.database.retention_days
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        with self.get_session() as session:
            # Delete old posts and their associated data
            old_posts = session.query(Post).filter(Post.collected_at < cutoff_date)
            deleted_count = old_posts.count()
            old_posts.delete()
            
            # Delete old alerts
            old_alerts = session.query(Alert).filter(Alert.created_at < cutoff_date)
            old_alerts.delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_count} old posts and associated data")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {
                'total_keywords': session.query(Keyword).filter_by(is_active=True).count(),
                'total_posts': session.query(Post).count(),
                'total_sentiment_scores': session.query(SentimentScore).count(),
                'active_alerts': session.query(Alert).filter_by(is_active=True).count(),
                'database_size_mb': self._get_db_size_mb(),
                'oldest_post': session.query(func.min(Post.posted_at)).scalar(),
                'newest_post': session.query(func.max(Post.posted_at)).scalar()
            }
            return stats
    
    def _get_db_size_mb(self) -> float:
        """Get database file size in MB."""
        try:
            size_bytes = os.path.getsize(self.db_path)
            return round(size_bytes / (1024 * 1024), 2)
        except OSError:
            return 0.0


# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager