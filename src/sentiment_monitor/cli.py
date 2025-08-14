"""Command Line Interface for Sentiment Monitor."""

import click
import logging
import time
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

# Rich for better CLI output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track, Progress
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich not available. Install with: pip install rich")

from .storage.database import get_db
from .storage.models import Keyword, Post, SentimentScore
from .collectors.reddit_collector import RedditCollector
from .collectors.hackernews_collector import HackerNewsCollector
from .analysis.sentiment_analyzer import SentimentAnalyzer
from .utils.config import get_config, get_secrets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
console = Console() if RICH_AVAILABLE else None
db = get_db()
config = get_config()


class SentimentMonitorCLI:
    """Main CLI class for Sentiment Monitor."""
    
    def __init__(self):
        self.db = db
        self.config = config
        self.console = console
        
        # Initialize collectors
        self.collectors = {
            'reddit': RedditCollector(),
            'hackernews': HackerNewsCollector()
        }
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        if self.console:
            self.console.print(f"[blue]INFO: {message}[/blue]")
        else:
            print(f"INFO: {message}")
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        if self.console:
            self.console.print(f"[green]SUCCESS: {message}[/green]")
        else:
            print(f"SUCCESS: {message}")
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        if self.console:
            self.console.print(f"[yellow]WARNING: {message}[/yellow]")
        else:
            print(f"WARNING: {message}")
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        if self.console:
            self.console.print(f"[red]ERROR: {message}[/red]")
        else:
            print(f"ERROR: {message}")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Real-Time Social Media Sentiment Monitor - Track public opinion across platforms."""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.obj['cli'] = SentimentMonitorCLI()


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration."""
    cli_obj = ctx.obj['cli']
    
    if cli_obj.console:
        # Rich status display
        layout = Layout()
        
        # Database status
        db_stats = cli_obj.db.get_database_stats()
        db_table = Table(title="Database Status")
        db_table.add_column("Metric", style="cyan")
        db_table.add_column("Value", style="yellow")
        
        db_table.add_row("Active Keywords", str(db_stats['total_keywords']))
        db_table.add_row("Total Posts", str(db_stats['total_posts']))
        db_table.add_row("Sentiment Scores", str(db_stats['total_sentiment_scores']))
        db_table.add_row("Active Alerts", str(db_stats['active_alerts']))
        db_table.add_row("Database Size", f"{db_stats['database_size_mb']} MB")
        
        # Collector status
        collector_table = Table(title="Data Collectors")
        collector_table.add_column("Platform", style="cyan")
        collector_table.add_column("Status", style="yellow")
        collector_table.add_column("Details", style="green")
        
        for name, collector in cli_obj.collectors.items():
            status_info = collector.test_connection()
            status = "Available" if status_info['available'] else "Unavailable"
            details = status_info.get('error', 'Working') if status_info.get('error') else 'Working'
            collector_table.add_row(name.capitalize(), status, details)
        
        # Sentiment analyzer status
        sentiment_info = cli_obj.sentiment_analyzer.get_model_info()
        sentiment_table = Table(title="Sentiment Analysis")
        sentiment_table.add_column("Model", style="cyan")
        sentiment_table.add_column("Status", style="yellow")
        sentiment_table.add_column("Version", style="green")
        
        for model_name in sentiment_info['available_models']:
            model_details = sentiment_info['model_details'][model_name]
            status = "Available" if model_details['available'] else "Unavailable"
            sentiment_table.add_row(
                model_name.capitalize(),
                status,
                model_details['model_version']
            )
        
        cli_obj.console.print(Panel.fit(db_table, title="System Status"))
        cli_obj.console.print(Panel.fit(collector_table))
        cli_obj.console.print(Panel.fit(sentiment_table))
        
    else:
        # Simple text status
        print("=== Sentiment Monitor Status ===")
        print(f"Database: {cli_obj.db.get_database_stats()}")
        print(f"Collectors: {[name for name in cli_obj.collectors.keys()]}")
        print(f"Sentiment Models: {cli_obj.sentiment_analyzer.get_model_info()['available_models']}")


@cli.group()
def keywords():
    """Manage monitoring keywords."""
    pass


@keywords.command('add')
@click.argument('keyword')
@click.pass_context
def add_keyword(ctx, keyword):
    """Add a new keyword to monitor."""
    cli_obj = ctx.obj['cli']
    
    try:
        keyword_obj = cli_obj.db.add_keyword(keyword)
        cli_obj.print_success(f"Added keyword: {keyword}")
        
        # Update config
        from .utils.config import config_manager
        current_keywords = cli_obj.config.keywords.get('default', [])
        if keyword not in current_keywords:
            current_keywords.append(keyword)
            config_manager.update_keywords(current_keywords)
        
    except Exception as e:
        cli_obj.print_error(f"Failed to add keyword: {e}")


@keywords.command('remove')
@click.argument('keyword')
@click.pass_context
def remove_keyword(ctx, keyword):
    """Remove a keyword from monitoring."""
    cli_obj = ctx.obj['cli']
    
    try:
        success = cli_obj.db.remove_keyword(keyword)
        if success:
            cli_obj.print_success(f"Removed keyword: {keyword}")
        else:
            cli_obj.print_warning(f"Keyword not found: {keyword}")
    except Exception as e:
        cli_obj.print_error(f"Failed to remove keyword: {e}")


@keywords.command('list')
@click.pass_context
def list_keywords(ctx):
    """List all active keywords."""
    cli_obj = ctx.obj['cli']
    
    try:
        keywords = cli_obj.db.get_active_keywords()
        
        if cli_obj.console:
            table = Table(title="Active Keywords")
            table.add_column("Keyword", style="cyan")
            table.add_column("Created", style="yellow")
            table.add_column("Updated", style="green")
            
            for keyword in keywords:
                table.add_row(
                    keyword.keyword,
                    keyword.created_at.strftime("%Y-%m-%d %H:%M"),
                    keyword.updated_at.strftime("%Y-%m-%d %H:%M")
                )
            
            cli_obj.console.print(table)
        else:
            print("Active Keywords:")
            for keyword in keywords:
                print(f"  - {keyword.keyword}")
                
    except Exception as e:
        cli_obj.print_error(f"Failed to list keywords: {e}")


@cli.command()
@click.option('--keyword', '-k', help='Specific keyword to collect for')
@click.option('--platform', '-p', type=click.Choice(['reddit', 'hackernews', 'all']), default='all', help='Platform to collect from')
@click.option('--limit', '-l', default=50, help='Maximum posts to collect per platform')
@click.pass_context
def collect(ctx, keyword, platform, limit):
    """Collect posts for keywords."""
    cli_obj = ctx.obj['cli']
    
    try:
        # Get keywords to process
        if keyword:
            keywords = [keyword]
            # Add keyword if it doesn't exist
            cli_obj.db.add_keyword(keyword)
        else:
            keyword_objs = cli_obj.db.get_active_keywords()
            keywords = [k.keyword for k in keyword_objs]
        
        if not keywords:
            cli_obj.print_warning("No keywords to collect for. Add keywords first.")
            return
        
        # Select platforms
        platforms = ['reddit', 'hackernews'] if platform == 'all' else [platform]
        
        cli_obj.print_info(f"Collecting posts for {len(keywords)} keywords from {', '.join(platforms)}")
        
        total_collected = 0
        
        for kw in keywords:
            cli_obj.print_info(f"Collecting for keyword: {kw}")
            
            for platform_name in platforms:
                if platform_name not in cli_obj.collectors:
                    continue
                
                collector = cli_obj.collectors[platform_name]
                if not collector.is_available():
                    cli_obj.print_warning(f"{platform_name} collector not available")
                    continue
                
                try:
                    posts = collector.collect_posts_for_keyword(kw, limit=limit)
                    
                    # Store posts in database
                    stored_count = 0
                    for post_data in posts:
                        if cli_obj.db.add_post(post_data):
                            stored_count += 1
                    
                    cli_obj.print_success(f"Collected {stored_count} new posts from {platform_name}")
                    total_collected += stored_count
                    
                except Exception as e:
                    cli_obj.print_error(f"Error collecting from {platform_name}: {e}")
        
        cli_obj.print_success(f"Total collected: {total_collected} posts")
        
    except Exception as e:
        cli_obj.print_error(f"Collection failed: {e}")


@cli.command()
@click.option('--keyword', '-k', help='Specific keyword to analyze')
@click.option('--limit', '-l', default=100, help='Maximum posts to analyze')
@click.pass_context
def analyze(ctx, keyword, limit):
    """Analyze sentiment for collected posts."""
    cli_obj = ctx.obj['cli']
    
    try:
        # Get posts to analyze
        with cli_obj.db.get_session() as session:
            query = session.query(Post).filter(Post.is_processed == False)
            
            if keyword:
                keyword_obj = session.query(Keyword).filter_by(keyword=keyword).first()
                if not keyword_obj:
                    cli_obj.print_error(f"Keyword '{keyword}' not found")
                    return
                query = query.filter(Post.keyword_id == keyword_obj.id)
            
            posts = query.limit(limit).all()
        
        if not posts:
            cli_obj.print_info("No posts to analyze")
            return
        
        cli_obj.print_info(f"Analyzing sentiment for {len(posts)} posts")
        
        analyzed_count = 0
        
        if cli_obj.console:
            # Use progress bar
            for post in track(posts, description="Analyzing..."):
                try:
                    # Analyze sentiment
                    results = cli_obj.sentiment_analyzer.analyze_text(post.content)
                    
                    # Store results
                    for result in results:
                        score_data = {
                            'post_id': post.id,
                            **result
                        }
                        cli_obj.db.add_sentiment_score(score_data)
                    
                    # Mark as processed
                    with cli_obj.db.get_session() as session:
                        post_obj = session.get(Post, post.id)
                        post_obj.is_processed = True
                        session.commit()
                    
                    analyzed_count += 1
                    
                except Exception as e:
                    cli_obj.print_warning(f"Error analyzing post {post.id}: {e}")
        else:
            # Simple progress
            for i, post in enumerate(posts):
                print(f"Analyzing {i+1}/{len(posts)}", end="\\r")
                # ... analysis code ...
                analyzed_count += 1
        
        cli_obj.print_success(f"Analyzed {analyzed_count} posts")
        
    except Exception as e:
        cli_obj.print_error(f"Analysis failed: {e}")


@cli.command()
@click.option('--keyword', '-k', help='Keyword to show dashboard for')
@click.option('--hours', '-h', default=24, help='Hours of data to show')
@click.option('--refresh', '-r', default=30, help='Refresh interval in seconds')
@click.pass_context
def dashboard(ctx, keyword, hours, refresh):
    """Show real-time sentiment dashboard."""
    cli_obj = ctx.obj['cli']
    
    if not cli_obj.console:
        cli_obj.print_error("Dashboard requires rich library. Install with: pip install rich")
        return
    
    try:
        # Get keywords
        if keyword:
            keywords = [keyword]
        else:
            keyword_objs = cli_obj.db.get_active_keywords()
            keywords = [k.keyword for k in keyword_objs[:3]]  # Show top 3
        
        if not keywords:
            cli_obj.print_warning("No keywords to display")
            return
        
        def generate_dashboard():
            layout = Layout()
            
            panels = []
            for kw in keywords:
                # Get sentiment summary
                summary = cli_obj.db.get_sentiment_summary(kw, hours=hours)
                recent_posts = cli_obj.db.get_recent_posts(kw, hours=hours, limit=5)
                
                # Create summary table
                summary_table = Table(title=f"📊 {kw}")
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", style="yellow")
                
                summary_table.add_row("Total Posts", str(summary['total_posts']))
                summary_table.add_row("Avg Sentiment", f"{summary['avg_sentiment']:.3f}")
                summary_table.add_row("Positive", str(summary['positive_count']))
                summary_table.add_row("Negative", str(summary['negative_count']))
                summary_table.add_row("Neutral", str(summary['neutral_count']))
                
                # Recent posts
                posts_table = Table(title="Recent Posts")
                posts_table.add_column("Time", style="dim")
                posts_table.add_column("Content", style="white")
                posts_table.add_column("Sentiment", style="green")
                
                for post in recent_posts[:3]:
                    # Get sentiment score
                    with cli_obj.db.get_session() as session:
                        score = session.query(SentimentScore).filter_by(post_id=post.id).first()
                        sentiment_str = f"{score.compound_score:.2f}" if score else "N/A"
                    
                    posts_table.add_row(
                        post.posted_at.strftime("%H:%M"),
                        post.content[:50] + "..." if len(post.content) > 50 else post.content,
                        sentiment_str
                    )
                
                panel = Panel.fit(
                    Columns([summary_table, posts_table], equal=True),
                    title=f"Sentiment Monitor - {kw}"
                )
                panels.append(panel)
            
            return Columns(panels, equal=True)
        
        # Live dashboard
        with Live(generate_dashboard(), refresh_per_second=1/refresh) as live:
            try:
                while True:
                    time.sleep(refresh)
                    live.update(generate_dashboard())
            except KeyboardInterrupt:
                cli_obj.print_info("Dashboard stopped")
        
    except Exception as e:
        cli_obj.print_error(f"Dashboard failed: {e}")


@cli.command()
@click.option('--keyword', '-k', required=True, help='Keyword to export data for')
@click.option('--output', '-o', default='sentiment_data.csv', help='Output file path')
@click.option('--hours', '-h', default=168, help='Hours of data to export (default: 7 days)')
@click.pass_context
def export(ctx, keyword, output, hours):
    """Export sentiment data to CSV."""
    cli_obj = ctx.obj['cli']
    
    try:
        import pandas as pd
        
        # Get sentiment trends
        trends = cli_obj.db.get_sentiment_trends(keyword, hours=hours)
        
        if not trends:
            cli_obj.print_warning(f"No data found for keyword '{keyword}'")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(trends)
        
        # Save to CSV
        df.to_csv(output, index=False)
        cli_obj.print_success(f"Exported {len(trends)} records to {output}")
        
    except ImportError:
        cli_obj.print_error("Export requires pandas. Install with: pip install pandas")
    except Exception as e:
        cli_obj.print_error(f"Export failed: {e}")


@cli.command()
@click.option('--keyword', '-k', help='Keyword to monitor (starts continuous monitoring)')
@click.option('--interval', '-i', default=300, help='Collection interval in seconds')
@click.pass_context
def monitor(ctx, keyword, interval):
    """Start continuous monitoring for keywords."""
    cli_obj = ctx.obj['cli']
    
    try:
        keywords = [keyword] if keyword else [k.keyword for k in cli_obj.db.get_active_keywords()]
        
        if not keywords:
            cli_obj.print_warning("No keywords to monitor")
            return
        
        cli_obj.print_info(f"Starting continuous monitoring for: {', '.join(keywords)}")
        cli_obj.print_info(f"Collection interval: {interval} seconds")
        cli_obj.print_info("Press Ctrl+C to stop")
        
        try:
            while True:
                for kw in keywords:
                    cli_obj.print_info(f"Collecting for: {kw}")
                    
                    # Collect from all platforms
                    for platform_name, collector in cli_obj.collectors.items():
                        if not collector.is_available():
                            continue
                        
                        try:
                            posts = collector.collect_posts_for_keyword(kw, limit=50)
                            stored_count = 0
                            
                            for post_data in posts:
                                if cli_obj.db.add_post(post_data):
                                    stored_count += 1
                            
                            if stored_count > 0:
                                cli_obj.print_success(f"Stored {stored_count} new posts from {platform_name}")
                        
                        except Exception as e:
                            cli_obj.print_warning(f"Error collecting from {platform_name}: {e}")
                
                # Analyze new posts
                cli_obj.print_info("Analyzing new posts...")
                ctx.invoke(analyze, limit=100)
                
                cli_obj.print_info(f"Waiting {interval} seconds until next collection...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            cli_obj.print_info("Monitoring stopped")
        
    except Exception as e:
        cli_obj.print_error(f"Monitoring failed: {e}")


if __name__ == '__main__':
    cli()