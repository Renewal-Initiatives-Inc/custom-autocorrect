"""Custom Autocorrect - Silent typo correction for Windows.

A lightweight Windows background application that silently corrects known typos
based on user-defined rules. The app monitors keystrokes system-wide, performs
corrections via backspace+retype, and passively tracks potential typos for user review.
"""

__version__ = "1.0.0"
__author__ = "Jeff Takle"

from .word_buffer import WordBuffer
from .keystroke_engine import KeystrokeEngine
from .rules import (
    Rule,
    RuleParser,
    RuleMatcher,
    RuleFileWatcher,
    backup_exists,
    create_backup,
    restore_from_backup,
    get_backup_info,
)
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
from .suggestions import (
    CorrectionPatternTracker,
    IgnoreList,
    SuggestionsFile,
    SUGGESTION_THRESHOLD,
)
from .single_instance import (
    SingleInstanceLock,
    is_another_instance_running,
    show_already_running_dialog,
)
from .startup import (
    is_startup_enabled,
    enable_startup,
    disable_startup,
    toggle_startup,
)

__all__ = [
    "WordBuffer",
    "KeystrokeEngine",
    "Rule",
    "RuleParser",
    "RuleMatcher",
    "RuleFileWatcher",
    "backup_exists",
    "create_backup",
    "restore_from_backup",
    "get_backup_info",
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
    "CorrectionPatternTracker",
    "IgnoreList",
    "SuggestionsFile",
    "SUGGESTION_THRESHOLD",
    "SingleInstanceLock",
    "is_another_instance_running",
    "show_already_running_dialog",
    "is_startup_enabled",
    "enable_startup",
    "disable_startup",
    "toggle_startup",
]
