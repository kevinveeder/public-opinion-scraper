"""Entry point for Streamlit dashboard."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the dashboard
from sentiment_monitor.dashboard.streamlit_app import main

if __name__ == "__main__":
    main()