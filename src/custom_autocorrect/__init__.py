"""Custom Autocorrect - Silent typo correction for Windows.

A lightweight Windows background application that silently corrects known typos
based on user-defined rules. The app monitors keystrokes system-wide, performs
corrections via backspace+retype, and passively tracks potential typos for user review.
"""

__version__ = "0.1.0"
__author__ = "Jeff Takle"

from .word_buffer import WordBuffer
from .keystroke_engine import KeystrokeEngine

__all__ = ["WordBuffer", "KeystrokeEngine"]
