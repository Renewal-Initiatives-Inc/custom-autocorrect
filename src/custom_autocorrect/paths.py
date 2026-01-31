"""Application path management.

Handles paths for:
- Documents/CustomAutocorrect/ folder structure
- rules.txt, suggestions.txt, corrections.log, etc.

This module centralizes all path handling to make it easy to:
- Test with custom paths
- Fall back gracefully if Documents folder isn't available
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default folder name in Documents
APP_FOLDER_NAME = "CustomAutocorrect"

# Sample rules.txt content for new installations
SAMPLE_RULES_CONTENT = """\
# Custom Autocorrect Rules
# Format: typo=correction
# Lines starting with # are comments
# Blank lines are ignored

# Example rules (uncomment to use):
# teh=the
# adn=and
# hte=the
# taht=that
# waht=what
"""


def get_documents_folder() -> Optional[Path]:
    """Get the user's Documents folder.

    Returns:
        Path to Documents folder, or None if not found.
    """
    # Try Windows-style first (most common use case)
    if os.name == "nt":
        # Use Windows FOLDERID_Documents via known folders API
        try:
            import ctypes.wintypes

            CSIDL_PERSONAL = 5  # Documents folder
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
            if buf.value:
                return Path(buf.value)
        except Exception as e:
            logger.debug(f"Windows folder detection failed: {e}")

    # Fall back to expanduser for cross-platform compatibility
    home = Path.home()

    # Check common locations
    for docs_name in ["Documents", "My Documents"]:
        docs_path = home / docs_name
        if docs_path.exists() and docs_path.is_dir():
            return docs_path

    # Last resort: try ~/Documents anyway (it might work)
    return home / "Documents"


def get_app_folder() -> Path:
    """Get the CustomAutocorrect folder path.

    This returns the path where the app stores its files:
    Documents/CustomAutocorrect/

    Returns:
        Path to the app folder (may not exist yet).
    """
    docs = get_documents_folder()
    if docs:
        return docs / APP_FOLDER_NAME

    # Fallback: use app directory (less ideal but works)
    logger.warning("Documents folder not found, using fallback location")
    return Path.home() / APP_FOLDER_NAME


def get_rules_path() -> Path:
    """Get path to rules.txt."""
    return get_app_folder() / "rules.txt"


def get_suggestions_path() -> Path:
    """Get path to suggestions.txt."""
    return get_app_folder() / "suggestions.txt"


def get_ignore_path() -> Path:
    """Get path to ignore.txt."""
    return get_app_folder() / "ignore.txt"


def get_corrections_log_path() -> Path:
    """Get path to corrections.log."""
    return get_app_folder() / "corrections.log"


def get_custom_words_path() -> Path:
    """Get path to custom-words.txt."""
    return get_app_folder() / "custom-words.txt"


def ensure_app_folder() -> Path:
    """Create the app folder if it doesn't exist.

    Returns:
        Path to the created/existing folder.

    Raises:
        OSError: If folder cannot be created.
    """
    folder = get_app_folder()

    if not folder.exists():
        try:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created app folder: {folder}")
        except OSError as e:
            logger.error(f"Failed to create app folder {folder}: {e}")
            raise

    return folder


def ensure_rules_file() -> Path:
    """Create rules.txt with sample content if it doesn't exist.

    Returns:
        Path to the rules file.
    """
    rules_path = get_rules_path()

    if not rules_path.exists():
        try:
            # Ensure folder exists first
            ensure_app_folder()

            # Create sample rules file
            rules_path.write_text(SAMPLE_RULES_CONTENT, encoding="utf-8")
            logger.info(f"Created sample rules file: {rules_path}")
        except OSError as e:
            logger.error(f"Failed to create rules file {rules_path}: {e}")
            raise

    return rules_path


def ensure_all_files() -> dict[str, Path]:
    """Ensure all app files exist, creating them if needed.

    Returns:
        Dictionary mapping file names to their paths.
    """
    ensure_app_folder()

    files = {
        "rules": ensure_rules_file(),
        "suggestions": get_suggestions_path(),
        "ignore": get_ignore_path(),
        "corrections_log": get_corrections_log_path(),
        "custom_words": get_custom_words_path(),
    }

    # Create empty files for those that don't exist (except rules which has content)
    for name, path in files.items():
        if name != "rules" and not path.exists():
            try:
                path.touch()
                logger.debug(f"Created empty file: {path}")
            except OSError as e:
                logger.warning(f"Failed to create {path}: {e}")

    return files
