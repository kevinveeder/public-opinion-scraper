# API Reference

This document provides detailed API reference for the Sentiment Monitor components.

## Database Models

### Keyword
Represents keywords being monitored for sentiment analysis.

**Fields:**
- `id` (Integer): Primary key
- `keyword` (String): The keyword text
- `is_active` (Boolean): Whether the keyword is actively monitored
- `created_at` (DateTime): When the keyword was added
- `updated_at` (DateTime): Last modification time

**Methods:**
```python
# Add keyword
keyword = db.add_keyword("bitcoin")

# Deactivate keyword
success = db.remove_keyword("bitcoin")

# Get active keywords
keywords = db.get_active_keywords()
```

### Platform
Represents social media platforms.

**Fields:**
- `id` (Integer): Primary key
- `name` (String): Platform name (reddit, hackernews, etc.)
- `is_active` (Boolean): Whether platform collection is enabled
- `created_at` (DateTime): When platform was added

### Post
Represents collected posts/comments from social media platforms.

**Fields:**
- `id` (Integer): Primary key
- `external_id` (String): Platform-specific post ID
- `platform_id` (Integer): Foreign key to Platform
- `keyword_id` (Integer): Foreign key to Keyword
- `title` (String): Post title
- `content` (Text): Post content
- `url` (String): Post URL
- `author` (String): Post author
- `created_at` (DateTime): When record was created
- `posted_at` (DateTime): When post was created on platform
- `collected_at` (DateTime): When post was collected
- `score` (Integer): Platform-specific score (upvotes, points, etc.)
- `comment_count` (Integer): Number of comments
- `metadata` (JSON): Additional platform-specific data
- `is_processed` (Boolean): Whether sentiment analysis was performed
- `is_duplicate` (Boolean): Whether post is a duplicate
- `is_spam` (Boolean): Whether post is identified as spam

### SentimentScore
Represents sentiment analysis results for posts.

**Fields:**
- `id` (Integer): Primary key
- `post_id` (Integer): Foreign key to Post
- `model_name` (String): Name of sentiment model used
- `model_version` (String): Version of the model
- `compound_score` (Float): Overall sentiment (-1 to 1)
- `positive_score` (Float): Positive sentiment component
- `negative_score` (Float): Negative sentiment component
- `neutral_score` (Float): Neutral sentiment component
- `confidence` (Float): Model confidence in prediction
- `processing_time` (Float): Time taken for analysis
- `created_at` (DateTime): When analysis was performed
- `raw_output` (JSON): Full model output

### Alert
Represents sentiment alerts and notifications.

**Fields:**
- `id` (Integer): Primary key
- `keyword_id` (Integer): Foreign key to Keyword
- `alert_type` (String): Type of alert (sentiment_threshold, volume_spike, etc.)
- `severity` (String): Alert severity (low, medium, high, critical)
- `message` (Text): Alert message
- `current_value` (Float): Current metric value
- `threshold_value` (Float): Threshold that was breached
- `is_active` (Boolean): Whether alert is active
- `is_acknowledged` (Boolean): Whether alert was acknowledged
- `acknowledged_at` (DateTime): When alert was acknowledged
- `created_at` (DateTime): When alert was created
- `resolved_at` (DateTime): When alert was resolved
- `metadata` (JSON): Additional alert data

## Data Collection APIs

### BaseCollector
Abstract base class for all data collectors.

**Methods:**
```python
class BaseCollector:
    def is_available(self) -> bool:
        """Check if collector is available and configured."""
        
    def collect_posts_for_keyword(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Collect posts for a specific keyword."""
        
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to data source."""
        
    def validate_post_data(self, post_data: Dict[str, Any]) -> bool:
        """Validate post data structure."""
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
```

### RedditCollector
Collects data from Reddit using PRAW.

**Methods:**
```python
reddit_collector = RedditCollector()

# Check availability
if reddit_collector.is_available():
    # Collect posts for keyword
    posts = reddit_collector.collect_posts_for_keyword("bitcoin", limit=50)
    
    # Test connection
    status = reddit_collector.test_connection()
    
    # Get trending topics
    trending = reddit_collector.collect_trending_topics(["technology", "news"])
```

**Configuration Requirements:**
```yaml
# secrets.yaml
reddit:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  user_agent: "YourApp/1.0"
```

### HackerNewsCollector
Collects data from Hacker News using their API.

**Methods:**
```python
hn_collector = HackerNewsCollector()

# Collect posts
posts = hn_collector.collect_posts_for_keyword("AI", limit=25)

# Test connection
status = hn_collector.test_connection()
```

## Sentiment Analysis APIs

### SentimentAnalyzer
Main sentiment analysis engine supporting multiple models.

**Methods:**
```python
analyzer = SentimentAnalyzer()

# Analyze single text
results = analyzer.analyze_text("This is a great product!")

# Analyze batch of texts
texts = ["Great!", "Terrible!", "Okay."]
batch_results = analyzer.analyze_batch(texts)

# Get weighted sentiment from multiple models
weighted = analyzer.get_weighted_sentiment(results)

# Get sentiment label
label = analyzer.get_sentiment_label(0.6)  # "positive"

# Check confidence threshold
is_high_conf = analyzer.is_high_confidence(0.8)  # True

# Get model information
model_info = analyzer.get_model_info()
```

**Result Format:**
```python
{
    'model_name': 'vader',
    'model_version': '3.3.2',
    'compound_score': 0.6,
    'positive_score': 0.8,
    'negative_score': 0.1,
    'neutral_score': 0.1,
    'confidence': 0.8,
    'processing_time': 0.05,
    'raw_output': {...}
}
```

### TextPreprocessor
Handles text preprocessing for sentiment analysis.

**Methods:**
```python
preprocessor = TextPreprocessor()

# Preprocess text
clean_text = preprocessor.preprocess("Check out this URL: https://example.com @user #hashtag")
# Result: "check out this url hashtag" (depending on config)
```

### TextAnalyzer
Advanced text analysis utilities.

**Methods:**
```python
analyzer = TextAnalyzer()

# Analyze negation patterns
negation_analysis = analyzer.analyze_negation_context("This is not good")

# Analyze intensifiers
intensifier_analysis = analyzer.analyze_intensifiers("This is very extremely good")

# Analyze emphasis patterns
emphasis_analysis = analyzer.analyze_emphasis("This is AMAZING!!!")

# Extract keywords
keywords = analyzer.extract_keywords(text, top_n=10)

# Comprehensive analysis
full_analysis = analyzer.comprehensive_analysis(text)
```

## Analytics APIs

### SentimentAnalytics
Advanced analytics and insights for sentiment data.

**Methods:**
```python
analytics = SentimentAnalytics()

# Trend analysis
trend = analytics.analyze_trends("bitcoin", hours=24)

# Momentum calculation
momentum = analytics.calculate_momentum("bitcoin", hours=24)

# Volume correlation analysis
correlation = analytics.analyze_volume_correlation("bitcoin", hours=24)

# Anomaly detection
anomalies = analytics.detect_anomalies("bitcoin", hours=24)

# Compare keywords
comparison = analytics.compare_keywords(["bitcoin", "ethereum"], hours=24)

# Check alert conditions
alerts = analytics.check_alert_conditions("bitcoin")

# Generate comprehensive insights
insights = analytics.generate_insights("bitcoin", hours=24)
```

**TrendAnalysis Result:**
```python
@dataclass
class TrendAnalysis:
    keyword: str
    period_hours: int
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1
    sentiment_change: float
    confidence_score: float
    data_points: int
    r_squared: float
```

## Database APIs

### DatabaseManager
Manages database connections and operations.

**Methods:**
```python
db = DatabaseManager()

# Keyword management
keyword = db.add_keyword("bitcoin")
success = db.remove_keyword("bitcoin")
keywords = db.get_active_keywords()

# Platform management
platform = db.get_platform_by_name("reddit")

# Post management
post = db.add_post(post_data)
recent_posts = db.get_recent_posts("bitcoin", hours=24, limit=100)

# Sentiment score management
score = db.add_sentiment_score(score_data)
trends = db.get_sentiment_trends("bitcoin", hours=24)
summary = db.get_sentiment_summary("bitcoin", hours=24)

# Alert management
alert = db.add_alert(alert_data)
active_alerts = db.get_active_alerts()

# Maintenance
db.cleanup_old_data(retention_days=30)
stats = db.get_database_stats()
```

## Configuration APIs

### ConfigManager
Manages application configuration from YAML files.

**Methods:**
```python
from sentiment_monitor.utils.config import get_config, get_secrets

# Get configuration
config = get_config()

# Get secrets
secrets = get_secrets()

# Access configuration sections
db_config = config.database
collection_config = config.collection
sentiment_config = config.sentiment

# Get Reddit configuration
reddit_config = config_manager.get_reddit_config()

# Update keywords
config_manager.update_keywords(["bitcoin", "ethereum", "tesla"])
```

## Alert Management APIs

### AlertManager
Manages alerts and notifications.

**Methods:**
```python
alert_manager = AlertManager()

# Check and create alerts
alerts = alert_manager.check_and_create_alerts("bitcoin")

# Get active alerts
active_alerts = alert_manager.get_active_alerts("bitcoin")

# Acknowledge alert
success = alert_manager.acknowledge_alert(alert_id)

# Resolve alert
success = alert_manager.resolve_alert(alert_id)

# Cleanup old alerts
count = alert_manager.cleanup_old_alerts(days=30)

# Get alert summary
summary = alert_manager.get_alert_summary()
```

## CLI APIs

The CLI is built using Click and provides programmatic access to all functionality.

**Basic Usage:**
```python
from sentiment_monitor.cli import SentimentMonitorCLI

cli = SentimentMonitorCLI()

# Access components
db = cli.db
config = cli.config
collectors = cli.collectors
sentiment_analyzer = cli.sentiment_analyzer

# Print methods
cli.print_info("Information message")
cli.print_success("Success message")
cli.print_warning("Warning message")
cli.print_error("Error message")
```

## Error Handling

All APIs use consistent error handling patterns:

**Database Errors:**
```python
try:
    result = db.add_post(post_data)
    if result is None:
        # Handle duplicate or validation error
        pass
except SQLAlchemyError as e:
    # Handle database error
    logger.error(f"Database error: {e}")
```

**Collection Errors:**
```python
try:
    posts = collector.collect_posts_for_keyword("bitcoin")
except PRAWException as e:
    # Handle Reddit API error
    logger.error(f"Reddit API error: {e}")
except requests.exceptions.RequestException as e:
    # Handle network error
    logger.error(f"Network error: {e}")
```

**Analysis Errors:**
```python
try:
    results = analyzer.analyze_text(text)
except Exception as e:
    # Sentiment analysis should not raise exceptions
    # but may return empty results or error indicators
    logger.error(f"Analysis error: {e}")
```

## Rate Limiting

All collectors implement rate limiting to respect API guidelines:

**Reddit:**
- 60 requests per minute for authenticated requests
- 10 requests per minute for unauthenticated requests

**Hacker News:**
- No official rate limits, but we use conservative delays
- 0.2 seconds between story requests
- 0.1 seconds between comment requests

**Implementation:**
```python
# Collectors automatically handle rate limiting
time.sleep(collector.get_rate_limit_delay())

# Manual rate limit handling
collector.handle_rate_limit(retry_after=30)
```

## Logging

All components use Python's logging module:

**Logger Names:**
- `sentiment_monitor.storage.database`
- `sentiment_monitor.collectors.reddit`
- `sentiment_monitor.collectors.hackernews`
- `sentiment_monitor.analysis.sentiment_analyzer`
- `sentiment_monitor.analysis.analytics`
- `sentiment_monitor.utils.alerts`

**Usage:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

## Performance Considerations

**Database Optimization:**
- Use indexed queries for time-based filtering
- Implement pagination for large result sets
- Regular cleanup of old data

**Memory Management:**
- Process posts in batches
- Use generators for large datasets
- Clear caches periodically

**API Efficiency:**
- Implement request caching where appropriate
- Use connection pooling
- Retry failed requests with exponential backoff

**Monitoring:**
- Track processing times
- Monitor memory usage
- Log performance metrics