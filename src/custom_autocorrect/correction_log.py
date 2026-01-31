"""Correction logging with rolling log file.

Phase 5 Implementation:
- Active window title detection
- Log format: timestamp | original -> corrected | window
- Log rotation (max 100 entries)
- Handle edge cases (unknown window, file locked)

Correctness Property CP5: For any state of corrections.log,
the file shall contain at most MAX_LOG_ENTRIES entries.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import get_corrections_log_path, ensure_app_folder

logger = logging.getLogger(__name__)

# Maximum number of log entries to keep (CP5)
MAX_LOG_ENTRIES = 100

# Retry settings for locked file handling
FILE_LOCK_RETRY_DELAY_MS = 50
FILE_LOCK_MAX_RETRIES = 3


def get_active_window_title() -> str:
    """Get the title of the currently active/foreground window.

    Uses Windows API (user32.dll) on Windows, returns "Unknown" on other
    platforms or if detection fails.

    Returns:
        Window title string, or "Unknown" if detection fails.
    """
    try:
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32

        # Get handle to foreground window
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "Unknown"

        # Get window title length
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "Unknown"

        # Create buffer and get window title
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)

        title = buffer.value.strip()
        return title if title else "Unknown"

    except (AttributeError, OSError, ImportError) as e:
        # Not on Windows or Windows API call failed
        logger.debug(f"Window title detection failed: {e}")
        return "Unknown"
    except Exception as e:
        # Catch-all for unexpected errors (fail safe)
        logger.debug(f"Unexpected error in window detection: {e}")
        return "Unknown"


def format_log_entry(
    original: str, corrected: str, window_title: str, timestamp: Optional[datetime] = None
) -> str:
    """Format a correction as a log entry string.

    Args:
        original: The typo as typed (with original casing).
        corrected: The corrected text (with applied casing).
        window_title: Title of the active window.
        timestamp: Optional timestamp (defaults to now).

    Returns:
        Formatted log entry string.

    Format:
        2026-01-31 14:23:15 | teh -> the | Chrome - Google Docs
    """
    if timestamp is None:
        timestamp = datetime.now()

    ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Use Unicode arrow for readability
    return f"{ts_str} | {original} \u2192 {corrected} | {window_title}"


def read_log_entries(log_path: Path) -> list[str]:
    """Read existing log entries from file.

    Args:
        log_path: Path to the log file.

    Returns:
        List of log entry strings (may be empty).
    """
    if not log_path.exists():
        return []

    try:
        content = log_path.read_text(encoding="utf-8")
        # Filter out empty lines
        entries = [line for line in content.splitlines() if line.strip()]
        return entries
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to read log file {log_path}: {e}")
        return []


def write_log_entries(log_path: Path, entries: list[str]) -> bool:
    """Write log entries to file.

    Args:
        log_path: Path to the log file.
        entries: List of log entry strings.

    Returns:
        True if successful, False on error.
    """
    try:
        # Ensure parent directory exists
        ensure_app_folder()

        content = "\n".join(entries)
        if entries:
            content += "\n"  # Trailing newline

        log_path.write_text(content, encoding="utf-8")
        return True
    except OSError as e:
        logger.warning(f"Failed to write log file {log_path}: {e}")
        return False


def rotate_log(entries: list[str], max_entries: int = MAX_LOG_ENTRIES) -> list[str]:
    """Remove oldest entries if list exceeds max size.

    This implements CP5: Log Rotation - the log shall contain at most
    max_entries entries.

    Args:
        entries: Current log entries.
        max_entries: Maximum allowed entries.

    Returns:
        Rotated list with at most max_entries items.
    """
    if len(entries) <= max_entries:
        return entries

    # Keep the newest entries (last max_entries)
    return entries[-max_entries:]


def log_correction(original: str, corrected: str) -> bool:
    """Log a correction to the rolling log file.

    Captures active window, formats entry, handles rotation.
    Follows fail-safe principle: app continues even if logging fails.

    Args:
        original: The typo as typed.
        corrected: The corrected text.

    Returns:
        True if logged successfully, False on error.
    """
    try:
        # Get context
        window_title = get_active_window_title()

        # Format entry
        entry = format_log_entry(original, corrected, window_title)

        # Get log file path
        log_path = get_corrections_log_path()

        # Read existing entries with retry for locked files
        entries = _read_with_retry(log_path)

        # Append new entry
        entries.append(entry)

        # Rotate if needed (CP5)
        entries = rotate_log(entries)

        # Write back with retry for locked files
        success = _write_with_retry(log_path, entries)

        if success:
            logger.debug(f"Logged correction: {entry}")

        return success

    except Exception as e:
        # Catch-all for unexpected errors (fail safe)
        logger.error(f"Unexpected error in log_correction: {e}")
        return False


def _read_with_retry(log_path: Path) -> list[str]:
    """Read log file with retry for locked files.

    Args:
        log_path: Path to the log file.

    Returns:
        List of log entries, or empty list on failure.
    """
    for attempt in range(FILE_LOCK_MAX_RETRIES):
        try:
            return read_log_entries(log_path)
        except PermissionError:
            if attempt < FILE_LOCK_MAX_RETRIES - 1:
                time.sleep(FILE_LOCK_RETRY_DELAY_MS / 1000.0)
            else:
                logger.warning(f"Log file locked, giving up after {FILE_LOCK_MAX_RETRIES} attempts")
                return []

    return []


def _write_with_retry(log_path: Path, entries: list[str]) -> bool:
    """Write log file with retry for locked files.

    Args:
        log_path: Path to the log file.
        entries: Log entries to write.

    Returns:
        True if successful, False on failure.
    """
    for attempt in range(FILE_LOCK_MAX_RETRIES):
        try:
            return write_log_entries(log_path, entries)
        except PermissionError:
            if attempt < FILE_LOCK_MAX_RETRIES - 1:
                time.sleep(FILE_LOCK_RETRY_DELAY_MS / 1000.0)
            else:
                logger.warning(f"Log file locked for writing, giving up after {FILE_LOCK_MAX_RETRIES} attempts")
                return False

    return False


def get_correction_count_from_log() -> int:
    """Get the number of corrections currently in the log.

    Useful for displaying statistics to the user.

    Returns:
        Number of log entries.
    """
    log_path = get_corrections_log_path()
    entries = read_log_entries(log_path)
    return len(entries)
