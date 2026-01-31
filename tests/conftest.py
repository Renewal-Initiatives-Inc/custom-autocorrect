"""Pytest configuration and fixtures for Custom Autocorrect tests."""

import sys
from pathlib import Path

# Add src to path so tests can import the package
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
