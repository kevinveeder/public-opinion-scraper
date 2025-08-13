# Setup Guide

This comprehensive guide will walk you through setting up the Real-Time Social Media Sentiment Monitor from scratch.

## Prerequisites

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 1GB free space
- **Internet**: Stable internet connection for API access

### Required Accounts
- **Reddit Account**: Free account for API access
- **Email Account** (Optional): For alert notifications
- **Slack Workspace** (Optional): For team notifications

## Step 1: Environment Setup

### 1.1 Install Python
If Python 3.8+ is not installed:

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer and check "Add Python to PATH"
3. Verify installation: `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.9

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.9 python3.9-pip python3.9-venv
```

### 1.2 Install Git
**Windows:** Download from [git-scm.com](https://git-scm.com/)
**macOS:** `brew install git` or use Xcode Command Line Tools
**Linux:** `sudo apt install git`

### 1.3 Clone Repository
```bash
git clone https://github.com/your-username/public-opinion-scraper.git
cd public-opinion-scraper
```

## Step 2: Python Environment

### 2.1 Create Virtual Environment
```bash
# Create virtual environment
python -m venv sentiment_monitor_env

# Activate virtual environment
# Windows:
sentiment_monitor_env\\Scripts\\activate

# macOS/Linux:
source sentiment_monitor_env/bin/activate
```

### 2.2 Upgrade pip
```bash
python -m pip install --upgrade pip
```

### 2.3 Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - praw (Reddit API)
# - requests, beautifulsoup4 (Web scraping)
# - vaderSentiment (Sentiment analysis)
# - transformers, torch (Advanced NLP)
# - pandas, numpy, scikit-learn (Data analysis)
# - sqlalchemy (Database)
# - streamlit, plotly (Dashboard)
# - click (CLI)
# - pydantic, pyyaml (Configuration)
# - pytest (Testing)
```

### 2.4 Verify Installation
```bash
# Test imports
python -c "import praw, vaderSentiment, pandas, streamlit; print('All packages imported successfully')"
```

## Step 3: Reddit API Setup

### 3.1 Create Reddit Application
1. **Login to Reddit**: Go to [reddit.com](https://reddit.com) and login
2. **Navigate to Apps**: Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
3. **Create New App**:
   - Click "Create App" or "Create Another App"
   - **Name**: "Sentiment Monitor"
   - **App type**: Select "script"
   - **Description**: "Real-time sentiment monitoring"
   - **About URL**: Leave blank
   - **Redirect URI**: `http://localhost:8080`
4. **Save Application**

### 3.2 Get API Credentials
After creating the app, you'll see:
- **Client ID**: 14-character string under the app name
- **Client Secret**: Longer string next to "secret"

### 3.3 Test Reddit API
```bash
# Test Reddit connection
python -c "
import praw
r = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='SentimentMonitor/1.0'
)
print('Reddit API connected successfully')
print('Rate limits:', r.auth.limits)
"
```

## Step 4: Configuration Setup

### 4.1 Create Configuration Directory
```bash
# Directory should already exist, but verify
ls config/
# Should show: config.yaml, secrets.yaml.example
```

### 4.2 Setup Secrets File
```bash
# Copy example secrets file
cp config/secrets.yaml.example config/secrets.yaml

# Edit the secrets file
nano config/secrets.yaml  # Linux/macOS
notepad config/secrets.yaml  # Windows
```

### 4.3 Configure Reddit Credentials
Edit `config/secrets.yaml`:
```yaml
# Reddit API Credentials
reddit:
  client_id: "YOUR_14_CHAR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  user_agent: "SentimentMonitor/1.0 by YourRedditUsername"
  username: "your_reddit_username"  # Optional
  password: "your_reddit_password"  # Optional
```

### 4.4 Configure Optional Services

**Email Notifications (Optional):**
```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  email: "your_email@gmail.com"
  password: "your_app_password"  # Use app-specific password for Gmail
```

**Slack Notifications (Optional):**
```yaml
slack:
  webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

### 4.5 Customize Main Configuration
Edit `config/config.yaml` if needed:
```yaml
# Adjust collection frequency
collection:
  polling_interval: 5  # minutes between collections

# Adjust sentiment thresholds
alerts:
  thresholds:
    very_negative: -0.8
    negative: -0.3
    positive: 0.3
    very_positive: 0.8
```

## Step 5: Database Initialization

### 5.1 Initialize Database
```bash
# Initialize database and create tables
python -c "
from src.sentiment_monitor.storage.database import get_db
db = get_db()
print('Database initialized successfully')
print('Database stats:', db.get_database_stats())
"
```

### 5.2 Verify Database Structure
```bash
# Check that database file was created
ls data/
# Should show: sentiment_monitor.db

# Check database size
du -h data/sentiment_monitor.db
```

## Step 6: First Run and Testing

### 6.1 Test System Status
```bash
# Check system status
python main.py status

# Should show:
# - Database status
# - Collector availability
# - Sentiment model status
```

### 6.2 Add Your First Keyword
```bash
# Add a keyword to monitor
python main.py keywords add bitcoin

# Verify keyword was added
python main.py keywords list
```

### 6.3 Test Data Collection
```bash
# Collect some initial data
python main.py collect --keyword bitcoin --limit 10

# Check what was collected
python main.py keywords list
```

### 6.4 Test Sentiment Analysis
```bash
# Analyze collected posts
python main.py analyze --keyword bitcoin

# This should process the collected posts
```

### 6.5 Launch Dashboard
```bash
# Start the web dashboard
streamlit run dashboard.py

# Should open browser to http://localhost:8501
```

## Step 7: Advanced Setup

### 7.1 Enable Advanced Sentiment Models
To use RoBERTa transformer model:

```bash
# Install additional dependencies (if not already installed)
pip install torch transformers

# Test transformer model
python -c "
from transformers import pipeline
sentiment_pipeline = pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')
print('RoBERTa model loaded successfully')
"
```

Enable in `config/config.yaml`:
```yaml
sentiment:
  models:
    vader:
      enabled: true
      weight: 0.4
    roberta:
      enabled: true  # Enable RoBERTa
      weight: 0.6
```

### 7.2 Setup Email Notifications
If using Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Use app password** in `config/secrets.yaml`

### 7.3 Setup Slack Notifications
1. **Create Slack App**:
   - Go to [api.slack.com](https://api.slack.com/apps)
   - Create new app
   - Enable Incoming Webhooks
   - Create webhook for your channel
2. **Add webhook URL** to `config/secrets.yaml`

### 7.4 Performance Optimization
For better performance:

```yaml
# config/config.yaml
performance:
  max_workers: 4  # Adjust based on CPU cores
  request_timeout: 30
  max_retries: 3

# Adjust collection settings
collection:
  max_posts_per_poll: 100  # Increase for more data
  platforms:
    reddit:
      enabled: true
      max_posts: 200  # Increase limit
```

## Step 8: Production Setup

### 8.1 Setup as System Service (Linux)
Create service file `/etc/systemd/system/sentiment-monitor.service`:
```ini
[Unit]
Description=Sentiment Monitor Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/public-opinion-scraper
Environment=PATH=/path/to/sentiment_monitor_env/bin
ExecStart=/path/to/sentiment_monitor_env/bin/python main.py monitor
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sentiment-monitor
sudo systemctl start sentiment-monitor
sudo systemctl status sentiment-monitor
```

### 8.2 Setup Scheduled Collection (Alternative)
Using cron for periodic collection:
```bash
# Edit crontab
crontab -e

# Add collection every 5 minutes
*/5 * * * * cd /path/to/public-opinion-scraper && /path/to/sentiment_monitor_env/bin/python main.py collect
```

### 8.3 Setup Log Rotation
Create `/etc/logrotate.d/sentiment-monitor`:
```
/path/to/public-opinion-scraper/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 your_username your_username
}
```

## Step 9: Monitoring and Maintenance

### 9.1 Health Checks
Create monitoring script `scripts/health_check.py`:
```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sentiment_monitor.storage.database import get_db
from sentiment_monitor.collectors.reddit_collector import RedditCollector

def health_check():
    try:
        # Check database
        db = get_db()
        stats = db.get_database_stats()
        print(f"✓ Database: {stats['total_posts']} posts")
        
        # Check Reddit
        reddit = RedditCollector()
        if reddit.is_available():
            print("✓ Reddit collector: Available")
        else:
            print("✗ Reddit collector: Unavailable")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)
```

### 9.2 Backup Strategy
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/sentiment-monitor"
SOURCE_DIR="/path/to/public-opinion-scraper"

mkdir -p $BACKUP_DIR

# Backup database
cp $SOURCE_DIR/data/sentiment_monitor.db $BACKUP_DIR/sentiment_monitor_$DATE.db

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C $SOURCE_DIR config/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Problem: ModuleNotFoundError
# Solution: Ensure virtual environment is activated
source sentiment_monitor_env/bin/activate  # macOS/Linux
sentiment_monitor_env\\Scripts\\activate    # Windows
```

**2. Reddit API Errors**
```bash
# Problem: 401 Unauthorized
# Solution: Check credentials in config/secrets.yaml

# Problem: 429 Rate Limited
# Solution: Reduce collection frequency in config.yaml
```

**3. Database Errors**
```bash
# Problem: Database locked
# Solution: Ensure only one instance is running

# Problem: No such table
# Solution: Reinitialize database
python -c "from src.sentiment_monitor.storage.database import get_db; get_db()"
```

**4. Dashboard Not Loading**
```bash
# Problem: Streamlit app won't start
# Solution: Check if port 8501 is available
lsof -i :8501  # Check what's using the port
streamlit run dashboard.py --server.port 8502  # Use different port
```

**5. Memory Issues**
```bash
# Problem: High memory usage
# Solution: Reduce batch sizes in config.yaml
collection:
  max_posts_per_poll: 25  # Reduce from default 50
```

### Debug Mode
Enable debug logging:
```python
# Add to your script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help
1. **Check logs**: `tail -f logs/sentiment_monitor.log`
2. **Run tests**: `pytest tests/`
3. **Check system status**: `python main.py status`
4. **Verify configuration**: `python -c "from src.sentiment_monitor.utils.config import get_config; print(get_config())"`

## Next Steps

Once setup is complete:

1. **Add more keywords**: `python main.py keywords add "artificial intelligence"`
2. **Start monitoring**: `python main.py monitor --interval 300`
3. **Explore dashboard**: Open `http://localhost:8501`
4. **Set up alerts**: Configure thresholds in `config/config.yaml`
5. **Explore analytics**: Use the CLI dashboard or web interface

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review the error logs
3. Ensure all prerequisites are met
4. Verify API credentials
5. Test individual components separately

The system is designed to be robust and self-healing, but proper setup is crucial for optimal performance.