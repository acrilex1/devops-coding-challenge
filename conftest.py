"""
Pytest configuration and fixtures.

This file ensures that the src module can be imported in tests.
"""

import sys
from pathlib import Path

# Add the project root to Python path so 'src' module can be imported
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
