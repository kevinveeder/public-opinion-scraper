"""Main entry point for Sentiment Monitor."""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from sentiment_monitor.cli import cli

if __name__ == '__main__':
    cli()