"""
Entry point for Exporo SME Export Assistant
This file provides easy access to run the application from the root directory
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from exporo.main import main

if __name__ == "__main__":
    main()