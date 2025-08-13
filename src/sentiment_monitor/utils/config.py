"""Configuration management utilities."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    path: str
    backup_interval_hours: int = 24
    retention_days: int = 30


class CollectionConfig(BaseModel):
    polling_interval: int = 3
    max_posts_per_poll: int = 50
    platforms: Dict[str, Any] = {}


class SentimentConfig(BaseModel):
    models: Dict[str, Any] = {}
    confidence_threshold: float = 0.7


class AlertsConfig(BaseModel):
    enabled: bool = True
    thresholds: Dict[str, float] = {}
    volume_threshold: int = 10
    rapid_change_threshold: float = 0.3


class DashboardConfig(BaseModel):
    title: str = "Real-Time Sentiment Monitor"
    refresh_interval_seconds: int = 30
    max_recent_posts: int = 20
    charts: Dict[str, Any] = {}


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file_path: str = "logs/sentiment_monitor.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"


class PerformanceConfig(BaseModel):
    max_workers: int = 4
    request_timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 1.0


class TextProcessingConfig(BaseModel):
    max_text_length: int = 1000
    detect_language: bool = True
    target_language: str = "en"
    remove_urls: bool = True
    remove_mentions: bool = False
    remove_hashtags: bool = False
    handle_emojis: bool = True


class Config(BaseModel):
    database: DatabaseConfig
    collection: CollectionConfig
    sentiment: SentimentConfig
    keywords: Dict[str, Any] = {}
    alerts: AlertsConfig
    dashboard: DashboardConfig
    logging: LoggingConfig
    performance: PerformanceConfig
    text_processing: TextProcessingConfig


class ConfigManager:
    """Manages application configuration from YAML files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent.parent / "config"
        self.config_file = self.config_dir / "config.yaml"
        self.secrets_file = self.config_dir / "secrets.yaml"
        self._config: Optional[Config] = None
        self._secrets: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Config:
        """Load and validate configuration from YAML file."""
        if self._config is None:
            try:
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                self._config = Config(**config_data)
                logger.info(f"Configuration loaded from {self.config_file}")
                
            except FileNotFoundError:
                logger.error(f"Configuration file not found: {self.config_file}")
                raise
            except ValidationError as e:
                logger.error(f"Configuration validation error: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                raise
        
        return self._config
    
    def load_secrets(self) -> Dict[str, Any]:
        """Load secrets from YAML file."""
        if self._secrets is None:
            try:
                if self.secrets_file.exists():
                    with open(self.secrets_file, 'r') as f:
                        self._secrets = yaml.safe_load(f) or {}
                    logger.info(f"Secrets loaded from {self.secrets_file}")
                else:
                    logger.warning(f"Secrets file not found: {self.secrets_file}")
                    self._secrets = {}
                    
            except Exception as e:
                logger.error(f"Error loading secrets: {e}")
                self._secrets = {}
        
        return self._secrets
    
    def get_config(self) -> Config:
        """Get loaded configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def get_secrets(self) -> Dict[str, Any]:
        """Get loaded secrets."""
        if self._secrets is None:
            return self.load_secrets()
        return self._secrets
    
    def get_reddit_config(self) -> Dict[str, str]:
        """Get Reddit API configuration."""
        secrets = self.get_secrets()
        reddit_config = secrets.get('reddit', {})
        
        if not reddit_config.get('client_id') or not reddit_config.get('client_secret'):
            logger.warning("Reddit API credentials not found in secrets.yaml")
        
        return reddit_config
    
    def update_keywords(self, keywords: list) -> None:
        """Update monitored keywords in configuration."""
        config = self.get_config()
        config.keywords['default'] = keywords
        
        # Save updated config back to file
        self._save_config(config)
    
    def _save_config(self, config: Config) -> None:
        """Save configuration back to YAML file."""
        try:
            config_dict = config.model_dump()
            with open(self.config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise


# Global config manager instance
config_manager = ConfigManager()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config_manager.get_config()

def get_secrets() -> Dict[str, Any]:
    """Get the global secrets instance."""
    return config_manager.get_secrets()