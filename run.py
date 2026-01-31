#!/usr/bin/env python
"""Entry point for PyInstaller builds.

This script imports the package properly so relative imports work.
"""

import sys

# Add src to path so the package can be found
from pathlib import Path
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from custom_autocorrect.main import main

if __name__ == "__main__":
    sys.exit(main())
