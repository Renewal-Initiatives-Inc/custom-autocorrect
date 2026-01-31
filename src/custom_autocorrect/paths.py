"""Application path management.

Handles paths for:
- Documents/CustomAutocorrect/ folder structure
- rules.txt, suggestions.txt, corrections.log, etc.
- Bundled resources (icon, dictionary) for PyInstaller builds

This module centralizes all path handling to make it easy to:
- Test with custom paths
- Fall back gracefully if Documents folder isn't available
- Access bundled resources in both development and packaged modes
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default folder name in Documents
APP_FOLDER_NAME = "CustomAutocorrect"


# =============================================================================
# Bundled Resource Helpers (for PyInstaller packaging)
# =============================================================================

def is_frozen() -> bool:
    """Check if running as a PyInstaller bundle.

    Returns:
        True if running as packaged executable, False in development.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_dir() -> Path:
    """Get the base directory for bundled resources.

    In development: returns the project root (parent of src/)
    In PyInstaller bundle: returns sys._MEIPASS temp directory

    Returns:
        Path to the base directory containing resources/.
    """
    if is_frozen():
        # PyInstaller extracts to a temp folder stored in sys._MEIPASS
        return Path(sys._MEIPASS)
    else:
        # Development mode: go up from paths.py to project root
        # paths.py is in src/custom_autocorrect/
        return Path(__file__).parent.parent.parent


def get_bundled_resource(relative_path: str) -> Optional[Path]:
    """Get path to a bundled resource file.

    Works in both development and PyInstaller bundle mode.

    Args:
        relative_path: Path relative to project root (e.g., 'resources/icon.png')

    Returns:
        Path to the resource if it exists, None otherwise.
    """
    resource_path = get_bundle_dir() / relative_path
    if resource_path.exists():
        return resource_path
    return None


def get_icon_path() -> Optional[Path]:
    """Get path to the bundled tray icon.

    Returns:
        Path to icon.png if found, None otherwise.
    """
    return get_bundled_resource('resources/icon.png')


def get_dictionary_path() -> Optional[Path]:
    """Get path to the bundled dictionary file.

    Returns:
        Path to words.txt if found, None otherwise.
    """
    return get_bundled_resource('resources/words.txt')


# =============================================================================
# User Data Folder Helpers (Documents/CustomAutocorrect/)
# =============================================================================

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

# Track which fallback location is being used (None = primary)
_active_fallback: Optional[str] = None


def test_write_permission(folder: Path) -> bool:
    """Test if a folder is writable.

    Creates and removes a temporary file to verify write access.

    Args:
        folder: Path to test.

    Returns:
        True if writable, False otherwise.
    """
    if not folder.exists():
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False

    test_file = folder / ".write_test"
    try:
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        return True
    except OSError:
        return False


def get_fallback_locations() -> list[tuple[str, Path]]:
    """Get ordered list of fallback storage locations.

    Returns:
        List of (name, path) tuples in priority order.
    """
    locations = []

    # 1. Primary: Documents folder
    docs = get_documents_folder()
    if docs:
        locations.append(("Documents", docs / APP_FOLDER_NAME))

    # 2. LOCALAPPDATA (Windows app data)
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        locations.append(("LocalAppData", Path(localappdata) / APP_FOLDER_NAME))

    # 3. APPDATA (Roaming, synced in some enterprise environments)
    appdata = os.environ.get("APPDATA")
    if appdata:
        locations.append(("AppData", Path(appdata) / APP_FOLDER_NAME))

    # 4. User home directory
    locations.append(("Home", Path.home() / APP_FOLDER_NAME))

    # 5. Current directory (last resort, may be read-only)
    locations.append(("Current", Path.cwd() / APP_FOLDER_NAME))

    return locations


def find_writable_location() -> Optional[tuple[str, Path]]:
    """Find the first writable location for app storage.

    Tries locations in priority order and returns the first writable one.

    Returns:
        Tuple of (location_name, path) or None if no writable location found.
    """
    global _active_fallback

    for name, path in get_fallback_locations():
        if test_write_permission(path):
            if name != "Documents":
                _active_fallback = name
                logger.warning(f"Using fallback storage location: {name} ({path})")
            else:
                _active_fallback = None
            return (name, path)

    logger.error("No writable storage location found!")
    return None


def get_active_storage_info() -> tuple[Optional[str], Path]:
    """Get information about the active storage location.

    Returns:
        Tuple of (fallback_name or None, path).
    """
    return (_active_fallback, get_app_folder())


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


# Cached app folder path (set after first writable location found)
_cached_app_folder: Optional[Path] = None


def get_app_folder() -> Path:
    """Get the CustomAutocorrect folder path.

    This returns the path where the app stores its files.
    On first call, tries Documents/CustomAutocorrect/ and falls back
    to alternative locations if not writable.

    Returns:
        Path to the app folder (may not exist yet).
    """
    global _cached_app_folder

    if _cached_app_folder is not None:
        return _cached_app_folder

    # Try primary location first (Documents)
    docs = get_documents_folder()
    if docs:
        primary = docs / APP_FOLDER_NAME
        if test_write_permission(primary):
            _cached_app_folder = primary
            return primary

    # Primary not writable, try fallbacks
    result = find_writable_location()
    if result:
        _, path = result
        _cached_app_folder = path
        return path

    # Last resort: return Documents anyway and let it fail later
    logger.error("No writable location found, using Documents (may fail)")
    if docs:
        return docs / APP_FOLDER_NAME
    return Path.home() / APP_FOLDER_NAME


def reset_app_folder_cache() -> None:
    """Reset the cached app folder path.

    Useful for testing or when storage location needs to be re-evaluated.
    """
    global _cached_app_folder, _active_fallback
    _cached_app_folder = None
    _active_fallback = None


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

    This function will try fallback locations if the primary location
    is not writable.

    Returns:
        Path to the created/existing folder.

    Raises:
        OSError: If no writable folder can be created.
    """
    folder = get_app_folder()

    if folder.exists():
        return folder

    try:
        folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created app folder: {folder}")
        return folder
    except OSError as e:
        logger.warning(f"Failed to create primary app folder {folder}: {e}")

        # Try fallback locations
        result = find_writable_location()
        if result:
            name, path = result
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback folder ({name}): {path}")
            return path

        # No fallback worked
        logger.error("Cannot create app folder in any location")
        raise OSError(f"Cannot create app folder: {e}")


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
