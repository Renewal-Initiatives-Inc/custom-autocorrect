"""Custom Autocorrect - Silent typo correction for Windows.

A lightweight Windows background application that silently corrects known typos
based on user-defined rules. The app monitors keystrokes system-wide, performs
corrections via backspace+retype, and passively tracks potential typos for user review.
"""

__version__ = "0.5.0"
__author__ = "Jeff Takle"

from .word_buffer import WordBuffer
from .keystroke_engine import KeystrokeEngine
from .rules import Rule, RuleParser, RuleMatcher, RuleFileWatcher
from .correction import (
    CorrectionEngine,
    apply_casing,
    detect_casing_pattern,
    perform_correction,
)
from .correction_log import (
    log_correction,
    get_active_window_title,
    format_log_entry,
    rotate_log,
    MAX_LOG_ENTRIES,
)
from .password_detect import is_password_field, reset_uia_cache

__all__ = [
    "WordBuffer",
    "KeystrokeEngine",
    "Rule",
    "RuleParser",
    "RuleMatcher",
    "RuleFileWatcher",
    "CorrectionEngine",
    "apply_casing",
    "detect_casing_pattern",
    "perform_correction",
    "log_correction",
    "get_active_window_title",
    "format_log_entry",
    "rotate_log",
    "MAX_LOG_ENTRIES",
    "is_password_field",
    "reset_uia_cache",
]
