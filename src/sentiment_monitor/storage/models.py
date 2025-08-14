"""Database models for sentiment monitoring data."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, 
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, VARCHAR
import json

Base = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = VARCHAR
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Keyword(Base):
    """Keywords being monitored."""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="keyword_rel")
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', active={self.is_active})>"


class Platform(Base):
    """Social media platforms."""
    __tablename__ = 'platforms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # reddit, hackernews, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="platform_rel")
    
    def __repr__(self):
        return f"<Platform(id={self.id}, name='{self.name}')>"


class Post(Base):
    """Individual posts/comments from social media platforms."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    
    # External IDs
    external_id = Column(String(255), nullable=False)  # Platform's post ID
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    
    # Content
    title = Column(Text)
    content = Column(Text, nullable=False)
    url = Column(Text)
    author = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime)  # When it was posted on the platform
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Engagement metrics
    score = Column(Integer, default=0)  # Reddit upvotes, HN points, etc.
    comment_count = Column(Integer, default=0)
    
    # Additional metadata (platform-specific)
    post_metadata = Column(JSONEncodedDict)
    
    # Processing flags
    is_processed = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    
    # Relationships
    platform_rel = relationship("Platform", back_populates="posts")
    keyword_rel = relationship("Keyword", back_populates="posts")
    sentiment_scores = relationship("SentimentScore", back_populates="post")
    
    # Indexes
    __table_args__ = (
        Index('idx_platform_external_id', 'platform_id', 'external_id'),
        Index('idx_keyword_posted_at', 'keyword_id', 'posted_at'),
        Index('idx_collected_at', 'collected_at'),
        UniqueConstraint('platform_id', 'external_id', name='uq_platform_external_id'),
    )
    
    def __repr__(self):
        return f"<Post(id={self.id}, platform={self.platform_rel.name if self.platform_rel else 'N/A'}, external_id='{self.external_id}')>"


class SentimentScore(Base):
    """Sentiment analysis results for posts."""
    __tablename__ = 'sentiment_scores'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)  # vader, roberta, etc.
    model_version = Column(String(50))
    
    # Sentiment scores
    compound_score = Column(Float)  # Overall sentiment (-1 to 1)
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)
    
    # Confidence and metadata
    confidence = Column(Float)
    processing_time = Column(Float)  # Time taken to process (seconds)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional model-specific data
    raw_output = Column(JSONEncodedDict)
    
    # Relationships
    post = relationship("Post", back_populates="sentiment_scores")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_model', 'post_id', 'model_name'),
        Index('idx_compound_score', 'compound_score'),
        Index('idx_confidence', 'confidence'),
    )
    
    def __repr__(self):
        return f"<SentimentScore(id={self.id}, post_id={self.post_id}, model='{self.model_name}', score={self.compound_score})>"


class Alert(Base):
    """Sentiment alerts and notifications."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # sentiment_threshold, volume_spike, rapid_change
    severity = Column(String(20))  # low, medium, high, critical
    message = Column(Text, nullable=False)
    
    # Alert data
    current_value = Column(Float)
    threshold_value = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Additional data
    alert_metadata = Column(JSONEncodedDict)
    
    # Relationships
    keyword_rel = relationship("Keyword")
    
    # Indexes
    __table_args__ = (
        Index('idx_keyword_active', 'keyword_id', 'is_active'),
        Index('idx_created_at', 'created_at'),
        Index('idx_severity', 'severity'),
    )
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', active={self.is_active})>"


class SentimentSummary(Base):
    """Aggregated sentiment data for analytics."""
    __tablename__ = 'sentiment_summaries'
    
    id = Column(Integer, primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False)
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly
    
    # Aggregate metrics
    post_count = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    median_sentiment = Column(Float)
    sentiment_std = Column(Float)
    
    # Distribution
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    
    # Engagement metrics
    avg_score = Column(Float)
    total_comments = Column(Integer, default=0)
    
    # Quality metrics
    avg_confidence = Column(Float)
    high_confidence_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    keyword_rel = relationship("Keyword")
    
    # Indexes
    __table_args__ = (
        Index('idx_keyword_period', 'keyword_id', 'period_start', 'period_end'),
        Index('idx_period_type', 'period_type'),
        UniqueConstraint('keyword_id', 'period_start', 'period_type', name='uq_keyword_period'),
    )
    
    def __repr__(self):
        return f"<SentimentSummary(id={self.id}, keyword_id={self.keyword_id}, period='{self.period_type}', avg_sentiment={self.avg_sentiment})>"