# Real-Time Social Media Sentiment Monitor

A comprehensive real-time sentiment monitoring system that tracks public opinion on user-specified keywords across multiple social media platforms. Built for data science portfolio and production use.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

## 🌟 Features

### Core Functionality
- **Real-time Data Collection**: Monitor Reddit, Hacker News, and other platforms every 2-5 minutes
- **Advanced Sentiment Analysis**: Multiple models including VADER and Hugging Face transformers
- **Intelligent Analytics**: Trend analysis, anomaly detection, and volume correlation
- **Interactive Dashboard**: Real-time Streamlit web interface with live charts
- **Command Line Interface**: Comprehensive CLI for all operations
- **Smart Alerting**: Email and Slack notifications for sentiment threshold breaches

### Advanced Features
- **Multi-Model Sentiment Analysis**: Weighted combination of VADER and RoBERTa models
- **Context-Aware Processing**: Negation handling, intensifier detection, emoji processing
- **Historical Analytics**: 7+ days of data retention with trend analysis
- **Anomaly Detection**: Statistical methods to identify unusual sentiment patterns
- **Entity Recognition**: Automatic extraction of companies, cryptocurrencies, and stock symbols
- **Comparative Analysis**: Side-by-side keyword performance comparison

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Reddit API credentials (free)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/public-opinion-scraper.git
cd public-opinion-scraper
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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

## 📊 Dashboard

The Streamlit dashboard provides real-time visualization of sentiment data:

- **Sentiment Gauge**: Current overall sentiment with emoji indicators
- **Time Series Charts**: Sentiment trends over time with confidence intervals
- **Distribution Analysis**: Pie charts showing positive/negative/neutral breakdown
- **Volume Correlation**: Scatter plots showing relationship between post volume and sentiment
- **Recent Posts Table**: Latest posts with sentiment scores and metadata
- **Real-time Updates**: Auto-refresh every 30 seconds

Access at: `http://localhost:8501`

## 🖥️ Command Line Interface

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

## ⚙️ Configuration

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

## 🔧 API Setup

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

## 📈 Analytics Features

### Trend Analysis
- **Direction Detection**: Improving, declining, or stable trends
- **Strength Measurement**: Statistical confidence in trend direction
- **Change Quantification**: Magnitude of sentiment shifts
- **Confidence Scoring**: Reliability of trend analysis

### Momentum Indicators
- **Moving Averages**: 5-period and 10-period sentiment averages
- **Momentum Signals**: Bullish, bearish, or neutral momentum
- **Volatility Measurement**: Sentiment stability assessment
- **Rate of Change**: Speed of sentiment shifts

### Anomaly Detection
- **Statistical Outliers**: Z-score based anomaly identification
- **Spike Detection**: Unusual positive or negative sentiment spikes
- **Severity Classification**: High, medium, or low impact anomalies
- **Temporal Analysis**: Time-based anomaly patterns

### Comparative Analysis
- **Multi-keyword Comparison**: Side-by-side performance metrics
- **Best/Worst Performers**: Automatic identification of top and bottom performers
- **Volume Analysis**: Post volume vs sentiment correlation
- **Range Analysis**: Sentiment and volume distribution across keywords

## 🚨 Alerting System

### Alert Types
- **Sentiment Thresholds**: Alerts when sentiment crosses predefined levels
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

## 🧪 Testing

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

## 📁 Project Structure

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

## 🔍 Sentiment Models

### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Optimized for social media text**
- **Handles negation, punctuation, and capitalization**
- **Fast processing, minimal resource requirements**
- **Good baseline for real-time analysis**

### RoBERTa (Robustly Optimized BERT Pretraining Approach)
- **State-of-the-art transformer model**
- **Fine-tuned on Twitter data**
- **High accuracy for nuanced sentiment**
- **Resource intensive but superior performance**

### Weighted Ensemble
- **Combines multiple models for better accuracy**
- **Configurable weights for different models**
- **Confidence-based result selection**
- **Fallback mechanisms for model failures**

## 📊 Data Models

### Database Schema
- **Keywords**: Monitored search terms
- **Platforms**: Social media sources (Reddit, HN, etc.)
- **Posts**: Collected content with metadata
- **Sentiment Scores**: Analysis results from multiple models
- **Alerts**: Triggered notifications and their status
- **Sentiment Summaries**: Aggregated analytics data

### Data Flow
1. **Collection**: Gather posts matching keywords from platforms
2. **Storage**: Store raw posts with metadata in database
3. **Analysis**: Process posts through sentiment models
4. **Aggregation**: Generate summaries and analytics
5. **Alerting**: Check thresholds and send notifications
6. **Visualization**: Display results in dashboard

## 🚀 Deployment

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Follow PEP 8 style guidelines
- Update documentation for API changes
- Use type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Kevin Veeder**
- Portfolio: [Your Portfolio URL]
- LinkedIn: [Your LinkedIn URL]
- Email: [Your Email]

## 🙏 Acknowledgments

- **VADER Sentiment**: Hutto, C.J. & Gilbert, E.E. (2014)
- **Hugging Face**: For providing excellent transformer models
- **Reddit API**: For enabling social media data access
- **Streamlit**: For making beautiful web apps easy
- **All contributors**: Who help improve this project

## 📈 Roadmap

### Upcoming Features
- [ ] Twitter/X integration
- [ ] Real-time WebSocket updates
- [ ] Machine learning model fine-tuning
- [ ] Advanced entity recognition
- [ ] Sentiment explanation generation
- [ ] Multi-language support
- [ ] Performance optimizations
- [ ] Cloud deployment guides

### Long-term Goals
- Support for more platforms (LinkedIn, Facebook, etc.)
- Advanced NLP features (topic modeling, aspect-based sentiment)
- Real-time streaming analytics
- Machine learning model training pipeline
- Enterprise features (user management, API access)

---

**Built with ❤️ for the data science community**