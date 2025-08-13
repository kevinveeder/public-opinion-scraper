"""Streamlit web dashboard for Sentiment Monitor."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

try:
    from sentiment_monitor.storage.database import get_db
    from sentiment_monitor.storage.models import Keyword, Post, SentimentScore
    from sentiment_monitor.utils.config import get_config
    from sentiment_monitor.collectors.reddit_collector import RedditCollector
    from sentiment_monitor.collectors.hackernews_collector import HackerNewsCollector
    from sentiment_monitor.analysis.sentiment_analyzer import SentimentAnalyzer
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Real-Time Sentiment Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize database and other components."""
    try:
        db = get_db()
        config = get_config()
        collectors = {
            'reddit': RedditCollector(),
            'hackernews': HackerNewsCollector()
        }
        sentiment_analyzer = SentimentAnalyzer()
        return db, config, collectors, sentiment_analyzer
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        return None, None, None, None

db, config, collectors, sentiment_analyzer = initialize_components()

if db is None:
    st.error("Failed to initialize application. Please check your configuration.")
    st.stop()

# Helper functions
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_active_keywords():
    """Get active keywords from database."""
    try:
        return [k.keyword for k in db.get_active_keywords()]
    except Exception as e:
        logger.error(f"Error getting keywords: {e}")
        return []

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_sentiment_data(keyword: str, hours: int = 24):
    """Get sentiment data for a keyword."""
    try:
        trends = db.get_sentiment_trends(keyword, hours=hours)
        summary = db.get_sentiment_summary(keyword, hours=hours)
        recent_posts = db.get_recent_posts(keyword, hours=hours, limit=20)
        return trends, summary, recent_posts
    except Exception as e:
        logger.error(f"Error getting sentiment data: {e}")
        return [], {}, []

def sentiment_color(score):
    """Get color for sentiment score."""
    if score > 0.1:
        return "#2E8B57"  # Green
    elif score < -0.1:
        return "#DC143C"  # Red
    else:
        return "#FFD700"  # Yellow

def sentiment_emoji(score):
    """Get emoji for sentiment score."""
    if score > 0.5:
        return "😄"
    elif score > 0.1:
        return "🙂"
    elif score > -0.1:
        return "😐"
    elif score > -0.5:
        return "🙁"
    else:
        return "😞"

# Main app
def main():
    """Main Streamlit application."""
    
    # Title and header
    st.title("📊 Real-Time Sentiment Monitor")
    st.markdown("Track public opinion across social media platforms")
    
    # Sidebar
    st.sidebar.title("🎛️ Controls")
    
    # Get keywords
    keywords = get_active_keywords()
    if not keywords:
        st.warning("No keywords found. Please add keywords using the CLI first.")
        st.code("python main.py keywords add <keyword>")
        return
    
    # Keyword selection
    selected_keyword = st.sidebar.selectbox(
        "Select Keyword",
        keywords,
        index=0
    )
    
    # Time range selection
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 6 hours", "Last 24 hours", "Last 3 days", "Last week"],
        index=1
    )
    
    hours_map = {
        "Last 6 hours": 6,
        "Last 24 hours": 24,
        "Last 3 days": 72,
        "Last week": 168
    }
    hours = hours_map[time_range]
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
    
    # Get data
    with st.spinner("Loading sentiment data..."):
        trends, summary, recent_posts = get_sentiment_data(selected_keyword, hours)
    
    if not trends and not summary:
        st.warning(f"No data found for keyword '{selected_keyword}' in the last {time_range.lower()}")
        return
    
    # Main dashboard layout
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics
    with col1:
        total_posts = summary.get('total_posts', 0)
        st.metric(
            "Total Posts",
            total_posts,
            delta=f"in {time_range.lower()}"
        )
    
    with col2:
        avg_sentiment = summary.get('avg_sentiment', 0)
        sentiment_change = "↗️" if avg_sentiment > 0 else "↘️" if avg_sentiment < 0 else "➡️"
        st.metric(
            "Avg Sentiment",
            f"{avg_sentiment:.3f}",
            delta=sentiment_change
        )
    
    with col3:
        positive_ratio = summary.get('positive_count', 0) / max(total_posts, 1) * 100
        st.metric(
            "Positive %",
            f"{positive_ratio:.1f}%",
            delta=f"{summary.get('positive_count', 0)} posts"
        )
    
    with col4:
        negative_ratio = summary.get('negative_count', 0) / max(total_posts, 1) * 100
        st.metric(
            "Negative %",
            f"{negative_ratio:.1f}%",
            delta=f"{summary.get('negative_count', 0)} posts"
        )
    
    # Sentiment gauge
    st.subheader("🎯 Current Sentiment")
    gauge_fig = create_sentiment_gauge(avg_sentiment)
    st.plotly_chart(gauge_fig, use_container_width=True)
    
    # Time series chart
    if trends:
        st.subheader("📈 Sentiment Over Time")
        timeseries_fig = create_timeseries_chart(trends, selected_keyword)
        st.plotly_chart(timeseries_fig, use_container_width=True)
    
    # Two column layout for additional charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Sentiment distribution
        st.subheader("📊 Sentiment Distribution")
        if summary:
            dist_fig = create_distribution_chart(summary)
            st.plotly_chart(dist_fig, use_container_width=True)
    
    with col_right:
        # Volume vs Sentiment correlation
        st.subheader("🔗 Volume vs Sentiment")
        if trends:
            correlation_fig = create_correlation_chart(trends)
            st.plotly_chart(correlation_fig, use_container_width=True)
    
    # Recent posts table
    st.subheader("📄 Recent Posts")
    if recent_posts:
        display_recent_posts(recent_posts)
    else:
        st.info("No recent posts found")
    
    # System status in sidebar
    st.sidebar.subheader("📊 System Status")
    show_system_status()
    
    # Data collection controls
    st.sidebar.subheader("🔄 Data Collection")
    if st.sidebar.button("Collect New Data"):
        collect_data(selected_keyword)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

def create_sentiment_gauge(sentiment_score):
    """Create sentiment gauge chart."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = sentiment_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Sentiment Score {sentiment_emoji(sentiment_score)}"},
        delta = {'reference': 0},
        gauge = {
            'axis': {'range': [-1, 1]},
            'bar': {'color': sentiment_color(sentiment_score)},
            'steps': [
                {'range': [-1, -0.5], 'color': "lightcoral"},
                {'range': [-0.5, -0.1], 'color': "lightyellow"},
                {'range': [-0.1, 0.1], 'color': "lightgray"},
                {'range': [0.1, 0.5], 'color': "lightgreen"},
                {'range': [0.5, 1], 'color': "darkgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_timeseries_chart(trends, keyword):
    """Create time series chart of sentiment."""
    df = pd.DataFrame(trends)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Sentiment Score', 'Confidence Level'),
        row_heights=[0.7, 0.3]
    )
    
    # Sentiment line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['sentiment'],
            mode='lines+markers',
            name='Sentiment',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ),
        row=1, col=1
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Confidence line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['confidence'],
            mode='lines',
            name='Confidence',
            line=dict(color='orange', width=1),
            fill='tonexty'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"Sentiment Timeline for '{keyword}'",
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Sentiment", range=[-1, 1], row=1, col=1)
    fig.update_yaxes(title_text="Confidence", range=[0, 1], row=2, col=1)
    
    return fig

def create_distribution_chart(summary):
    """Create sentiment distribution pie chart."""
    labels = ['Positive', 'Neutral', 'Negative']
    values = [
        summary.get('positive_count', 0),
        summary.get('neutral_count', 0),
        summary.get('negative_count', 0)
    ]
    colors = ['#2E8B57', '#FFD700', '#DC143C']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.3
    )])
    
    fig.update_layout(
        title="Sentiment Distribution",
        height=400
    )
    
    return fig

def create_correlation_chart(trends):
    """Create volume vs sentiment scatter plot."""
    df = pd.DataFrame(trends)
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Group by hour to get volume
    hourly_stats = df.groupby('hour').agg({
        'sentiment': 'mean',
        'timestamp': 'count'
    }).rename(columns={'timestamp': 'volume'})
    
    fig = go.Figure(data=go.Scatter(
        x=hourly_stats['volume'],
        y=hourly_stats['sentiment'],
        mode='markers',
        marker=dict(
            size=10,
            color=hourly_stats['sentiment'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Sentiment")
        ),
        text=[f"Hour: {h}" for h in hourly_stats.index],
        textposition="top center"
    ))
    
    fig.update_layout(
        title="Volume vs Sentiment by Hour",
        xaxis_title="Post Volume",
        yaxis_title="Average Sentiment",
        height=400
    )
    
    return fig

def display_recent_posts(posts):
    """Display recent posts in a table."""
    posts_data = []
    
    for post in posts[:10]:  # Show top 10
        # Get sentiment score
        with db.get_session() as session:
            score = session.query(SentimentScore).filter_by(post_id=post.id).first()
            sentiment_score = score.compound_score if score else None
        
        posts_data.append({
            'Time': post.posted_at.strftime("%m/%d %H:%M"),
            'Platform': post.platform_rel.name.capitalize() if post.platform_rel else 'Unknown',
            'Content': post.content[:100] + "..." if len(post.content) > 100 else post.content,
            'Sentiment': f"{sentiment_score:.3f}" if sentiment_score is not None else "N/A",
            'Score': post.score,
            'Author': post.author[:20] if post.author else "Anonymous"
        })
    
    if posts_data:
        df = pd.DataFrame(posts_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No posts to display")

def show_system_status():
    """Show system status in sidebar."""
    try:
        # Database stats
        db_stats = db.get_database_stats()
        st.write("**Database:**")
        st.write(f"• Posts: {db_stats['total_posts']}")
        st.write(f"• Keywords: {db_stats['total_keywords']}")
        st.write(f"• Size: {db_stats['database_size_mb']} MB")
        
        # Collector status
        st.write("**Collectors:**")
        for name, collector in collectors.items():
            status = "🟢" if collector.is_available() else "🔴"
            st.write(f"• {name.capitalize()}: {status}")
        
        # Sentiment analyzer status
        st.write("**Sentiment Analysis:**")
        model_info = sentiment_analyzer.get_model_info()
        for model in model_info['available_models']:
            st.write(f"• {model.capitalize()}: 🟢")
        
    except Exception as e:
        st.error(f"Error getting status: {e}")

def collect_data(keyword):
    """Collect new data for keyword."""
    try:
        with st.spinner(f"Collecting data for '{keyword}'..."):
            total_collected = 0
            
            for name, collector in collectors.items():
                if collector.is_available():
                    posts = collector.collect_posts_for_keyword(keyword, limit=25)
                    
                    stored_count = 0
                    for post_data in posts:
                        if db.add_post(post_data):
                            stored_count += 1
                    
                    total_collected += stored_count
            
            if total_collected > 0:
                st.success(f"Collected {total_collected} new posts!")
                # Clear cache to show new data
                st.cache_data.clear()
            else:
                st.info("No new posts found")
    
    except Exception as e:
        st.error(f"Error collecting data: {e}")

if __name__ == "__main__":
    main()