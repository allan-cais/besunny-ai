#!/usr/bin/env python3
"""
Simple entry point for Railway backend service
"""

import os
import sys
from pathlib import Path

# Add the parent backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Import and run the actual backend
from start import main

if __name__ == "__main__":
    main()
