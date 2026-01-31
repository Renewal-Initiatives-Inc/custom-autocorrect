"""Entry point for running custom_autocorrect as a module.

Usage:
    python -m custom_autocorrect
    python -m custom_autocorrect --debug
"""

import sys
from .main import main

if __name__ == "__main__":
    sys.exit(main())
