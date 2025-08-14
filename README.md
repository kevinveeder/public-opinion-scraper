# Real-Time Social Media Sentiment Monitor

A real-time sentiment monitoring system that tracks public opinion on specified keywords across multiple social media platforms. The system collects posts from Reddit and Hacker News, analyzes their sentiment using multiple machine learning models, and provides insights through both a web dashboard and command-line interface.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

## Features

### Core Functionality
- **Real-time Data Collection**: Automatically collects posts from Reddit and Hacker News every 2-5 minutes
- **Sentiment Analysis**: Uses multiple models including VADER and Hugging Face transformers for accuracy
- **Analytics**: Provides trend analysis, anomaly detection, and volume correlation insights
- **Web Dashboard**: Interactive Streamlit interface with live charts and real-time updates
- **Command Line Interface**: Complete CLI for managing keywords, collecting data, and monitoring
- **Alerting**: Email and Slack notifications when sentiment crosses configured thresholds

### Additional Features
- **Multi-Model Analysis**: Combines VADER and RoBERTa models with configurable weights
- **Text Processing**: Handles negation, intensifiers, and emoji processing for better accuracy
- **Historical Data**: Stores data for trend analysis with configurable retention periods
- **Anomaly Detection**: Uses statistical methods to identify unusual sentiment patterns
- **Entity Recognition**: Extracts companies, cryptocurrencies, and stock symbols from text
- **Comparative Analysis**: Compare sentiment across multiple keywords simultaneously

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Reddit API credentials (free)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kevinveeder/public-opinion-scraper.git
cd public-opinion-scraper
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate # On Mac: source venv/bin/activate  
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup configuration**
```bash
# Copy example secrets file
cp config/secrets.yaml.example config/secrets.yaml

# Edit with your API credentials
nano config/secrets.yaml
```

5. **Add your first keyword**
```bash
python main.py keywords add bitcoin
```

6. **Start collecting data**
```bash
python main.py collect --keyword bitcoin --limit 50
```

7. **Analyze sentiment**
```bash
python main.py analyze --keyword bitcoin
```

8. **Launch dashboard**
```bash
streamlit run dashboard.py
```

## Dashboard

The Streamlit dashboard provides real-time visualization of sentiment data:

- **Sentiment Gauge**: Shows current overall sentiment score
- **Time Series Charts**: Displays sentiment trends over time with confidence intervals
- **Distribution Analysis**: Pie charts showing positive, negative, and neutral post breakdown
- **Volume Correlation**: Scatter plots showing relationship between post volume and sentiment
- **Recent Posts Table**: Latest posts with sentiment scores and metadata
- **Real-time Updates**: Automatically refreshes every 30 seconds

Access the dashboard at: `http://localhost:8501`

## Command Line Interface

### Keyword Management
```bash
# Add keywords to monitor
python main.py keywords add "artificial intelligence"
python main.py keywords add tesla
python main.py keywords add bitcoin

# List active keywords
python main.py keywords list

# Remove keyword
python main.py keywords remove bitcoin
```

### Data Collection
```bash
# Collect for specific keyword
python main.py collect --keyword bitcoin --limit 100

# Collect from specific platform
python main.py collect --platform reddit --limit 50

# Collect for all active keywords
python main.py collect
```

### Sentiment Analysis
```bash
# Analyze recent posts
python main.py analyze --keyword bitcoin --limit 100

# Analyze all unprocessed posts
python main.py analyze
```

### Real-time Monitoring
```bash
# Start continuous monitoring
python main.py monitor --keyword bitcoin --interval 300

# Monitor all keywords
python main.py monitor --interval 180
```

### Dashboard and Export
```bash
# Live CLI dashboard
python main.py dashboard --keyword bitcoin --hours 24

# Export data to CSV
python main.py export --keyword bitcoin --output bitcoin_sentiment.csv
```

### System Status
```bash
# Check system status
python main.py status
```

## Configuration

### Main Configuration (`config/config.yaml`)
```yaml
# Database settings
database:
  path: "data/sentiment_monitor.db"
  retention_days: 30

# Collection settings
collection:
  polling_interval: 3  # minutes
  max_posts_per_poll: 50
  platforms:
    reddit:
      enabled: true
      subreddits: ["all", "news", "technology"]

# Sentiment analysis
sentiment:
  models:
    vader:
      enabled: true
      weight: 0.4
    roberta:
      enabled: true
      weight: 0.6
  confidence_threshold: 0.7

# Alerting
alerts:
  enabled: true
  thresholds:
    very_negative: -0.8
    negative: -0.3
    positive: 0.3
    very_positive: 0.8
```

### API Credentials (`config/secrets.yaml`)
```yaml
# Reddit API (required)
reddit:
  client_id: "your_reddit_client_id"
  client_secret: "your_reddit_client_secret"
  user_agent: "SentimentMonitor/1.0 by Kevin Veeder"

# Email notifications (optional)
email:
  smtp_server: "smtp.gmail.com"
  email: "your_email@gmail.com"
  password: "your_app_password"

# Slack notifications (optional)
slack:
  webhook_url: "your_slack_webhook_url"
```

## API Setup

### Reddit API Setup
1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" as application type
4. Note your `client_id` and `client_secret`
5. Add credentials to `config/secrets.yaml`

### Optional APIs
- **News API**: For additional news sources
- **Hugging Face**: For advanced transformer models
- **Email**: For alert notifications
- **Slack**: For team notifications

## Analytics Features

### Trend Analysis
- **Direction Detection**: Identifies improving, declining, or stable trends
- **Strength Measurement**: Provides statistical confidence in trend direction
- **Change Quantification**: Measures magnitude of sentiment shifts
- **Confidence Scoring**: Assesses reliability of trend analysis

### Momentum Indicators
- **Moving Averages**: Calculates 5-period and 10-period sentiment averages
- **Momentum Signals**: Identifies bullish, bearish, or neutral momentum
- **Volatility Measurement**: Assesses sentiment stability
- **Rate of Change**: Measures speed of sentiment shifts

### Anomaly Detection
- **Statistical Outliers**: Uses Z-score based identification methods
- **Spike Detection**: Identifies unusual positive or negative sentiment spikes
- **Severity Classification**: Categorizes anomalies as high, medium, or low impact
- **Temporal Analysis**: Analyzes time-based anomaly patterns

### Comparative Analysis
- **Multi-keyword Comparison**: Provides side-by-side performance metrics
- **Performance Ranking**: Identifies top and bottom performing keywords
- **Volume Analysis**: Analyzes relationship between post volume and sentiment
- **Distribution Analysis**: Shows sentiment and volume distribution across keywords

## Alerting System

### Alert Types
- **Sentiment Thresholds**: Triggers when sentiment crosses predefined levels
- **Volume Spikes**: Notifications for unusual activity levels
- **Rapid Changes**: Alerts for sudden sentiment shifts
- **Anomaly Detection**: Notifications for statistical outliers

### Notification Channels
- **Email**: SMTP-based email notifications
- **Slack**: Webhook-based team notifications
- **CLI**: Console-based alerts during monitoring

### Alert Management
```bash
# Check active alerts (via dashboard or database queries)
# Acknowledge alerts to prevent repeated notifications
# Configure thresholds in config.yaml
```

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/sentiment_monitor

# Run specific test file
pytest tests/test_sentiment_analysis.py

# Run with verbose output
pytest -v
```

### Test Coverage
- **Database Operations**: CRUD operations, data integrity
- **Sentiment Analysis**: Model accuracy, text preprocessing
- **Data Collection**: API integration, error handling
- **Analytics**: Trend analysis, anomaly detection
- **Configuration**: Settings validation, secret management

## Project Structure

```
public-opinion-scraper/
├── src/sentiment_monitor/          # Main package
│   ├── analysis/                   # Sentiment analysis & analytics
│   │   ├── sentiment_analyzer.py   # Multi-model sentiment analysis
│   │   ├── text_utils.py          # Text processing utilities
│   │   └── analytics.py           # Advanced analytics & insights
│   ├── collectors/                 # Data collection modules
│   │   ├── base_collector.py      # Abstract base collector
│   │   ├── reddit_collector.py    # Reddit data collection
│   │   └── hackernews_collector.py # Hacker News collection
│   ├── storage/                    # Database & data management
│   │   ├── models.py              # SQLAlchemy models
│   │   └── database.py            # Database operations
│   ├── dashboard/                  # Web interface
│   │   └── streamlit_app.py       # Streamlit dashboard
│   ├── utils/                      # Utilities
│   │   ├── config.py              # Configuration management
│   │   └── alerts.py              # Alert management
│   └── cli.py                     # Command line interface
├── tests/                         # Test suite
├── config/                        # Configuration files
├── data/                          # Database files
├── logs/                          # Log files
├── main.py                        # CLI entry point
├── dashboard.py                   # Dashboard entry point
└── requirements.txt               # Dependencies
```

## Sentiment Models

### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- Optimized for social media text analysis
- Handles negation, punctuation, and capitalization effectively
- Fast processing with minimal resource requirements
- Provides good baseline accuracy for real-time analysis

### RoBERTa (Robustly Optimized BERT Pretraining Approach)
- State-of-the-art transformer model for sentiment analysis
- Fine-tuned specifically on Twitter data
- Provides high accuracy for nuanced sentiment detection
- More resource intensive but offers superior performance

### Weighted Ensemble
- Combines multiple models for improved accuracy
- Configurable weights allow customization for different use cases
- Uses confidence-based result selection
- Includes fallback mechanisms for model failures

## Data Models

### Database Schema
- **Keywords**: Stores monitored search terms
- **Platforms**: Contains social media sources (Reddit, Hacker News, etc.)
- **Posts**: Stores collected content with metadata
- **Sentiment Scores**: Contains analysis results from multiple models
- **Alerts**: Tracks triggered notifications and their status
- **Sentiment Summaries**: Stores aggregated analytics data

### Data Flow
1. **Collection**: Gather posts matching keywords from platforms
2. **Storage**: Store raw posts with metadata in database
3. **Analysis**: Process posts through sentiment models
4. **Aggregation**: Generate summaries and analytics
5. **Alerting**: Check thresholds and send notifications
6. **Visualization**: Display results in dashboard

## Deployment

### Local Development
```bash
# Standard installation for development
pip install -r requirements.txt
python main.py monitor
```

### Production Deployment
```bash
# Install with production dependencies
pip install -r requirements.txt

# Set up as service (Linux)
sudo systemctl enable sentiment-monitor
sudo systemctl start sentiment-monitor

# Set up scheduled collection (cron)
*/5 * * * * /path/to/venv/bin/python /path/to/main.py collect
```

### Docker Deployment
```dockerfile
# Example Dockerfile (create as needed)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "monitor"]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Follow PEP 8 style guidelines
- Update documentation for API changes
- Use type hints where appropriate

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **VADER Sentiment**: Hutto, C.J. & Gilbert, E.E. (2014)
- **Hugging Face**: For providing transformer models and infrastructure
- **Reddit API**: For enabling social media data access
- **Streamlit**: For web application framework
- **Contributors**: All who help improve this project

## Roadmap

### Upcoming Features
- Twitter/X integration
- Real-time WebSocket updates
- Machine learning model fine-tuning
- Advanced entity recognition
- Sentiment explanation generation
- Multi-language support
- Performance optimizations
- Cloud deployment guides

### Long-term Goals
- Support for additional platforms (LinkedIn, Facebook, etc.)
- Advanced NLP features (topic modeling, aspect-based sentiment)
- Real-time streaming analytics
- Machine learning model training pipeline
- Enterprise features (user management, API access)
