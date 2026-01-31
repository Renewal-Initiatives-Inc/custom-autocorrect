"""Windows Startup folder integration.

Allows Custom Autocorrect to start automatically when Windows boots.

The app creates a shortcut (.lnk) in the user's Startup folder:
%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\

Usage:
    from custom_autocorrect.startup import enable_startup, disable_startup

    if enable_startup():
        print("App will start with Windows")

    if disable_startup():
        print("Auto-start disabled")
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SHORTCUT_NAME = "Custom Autocorrect.lnk"


def get_startup_folder() -> Optional[Path]:
    """Get the Windows Startup folder path.

    Returns:
        Path to Startup folder, or None if not found.
    """
    if os.name != "nt":
        logger.warning("Startup folder only available on Windows")
        return None

    # Use APPDATA environment variable
    appdata = os.environ.get("APPDATA")
    if not appdata:
        logger.warning("APPDATA environment variable not set")
        return None

    startup = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    if not startup.exists():
        logger.warning(f"Startup folder does not exist: {startup}")
        return None

    return startup


def get_shortcut_path() -> Optional[Path]:
    """Get the path where the shortcut would be created.

    Returns:
        Path to CustomAutocorrect.lnk, or None if startup folder unavailable.
    """
    startup = get_startup_folder()
    if not startup:
        return None
    return startup / SHORTCUT_NAME


def is_startup_enabled() -> bool:
    """Check if auto-start with Windows is enabled.

    Returns:
        True if shortcut exists in Startup folder.
    """
    shortcut = get_shortcut_path()
    if not shortcut:
        return False
    return shortcut.exists()


def get_executable_path() -> Path:
    """Get the path to the current executable or script.

    Returns:
        Path to CustomAutocorrect.exe or the main.py script.
    """
    from .paths import is_frozen

    if is_frozen():
        # Running as PyInstaller bundle
        return Path(sys.executable)
    else:
        # Running as script - use pythonw with module
        return Path(sys.executable)


def get_launch_command() -> tuple[str, str]:
    """Get the command to launch the application.

    Returns:
        Tuple of (target_path, arguments) for the shortcut.
    """
    from .paths import is_frozen

    if is_frozen():
        # Direct executable
        return str(Path(sys.executable)), ""
    else:
        # Python module - use pythonw to avoid console
        python_path = sys.executable
        # Try to use pythonw instead of python for no console
        pythonw = Path(python_path).parent / "pythonw.exe"
        if pythonw.exists():
            python_path = str(pythonw)
        return python_path, "-m custom_autocorrect"


def enable_startup() -> bool:
    """Enable auto-start with Windows.

    Creates a shortcut in the Startup folder.

    Returns:
        True if successful, False otherwise.
    """
    shortcut_path = get_shortcut_path()
    if not shortcut_path:
        logger.error("Cannot determine Startup folder")
        return False

    try:
        import win32com.client
    except ImportError:
        logger.error("win32com not available, cannot create shortcut")
        return False

    try:
        target, arguments = get_launch_command()

        # Create shortcut using Windows Shell
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(shortcut_path))

        shortcut.TargetPath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = str(Path(target).parent)
        shortcut.Description = "Custom Autocorrect - Silent typo correction"

        # Try to set icon
        from .paths import get_icon_path
        icon_path = get_icon_path()
        if icon_path:
            # For ICO files
            ico_path = icon_path.parent / "icon.ico"
            if ico_path.exists():
                shortcut.IconLocation = str(ico_path)

        shortcut.save()

        logger.info(f"Created startup shortcut: {shortcut_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create startup shortcut: {e}")
        return False


def disable_startup() -> bool:
    """Disable auto-start with Windows.

    Removes the shortcut from the Startup folder.

    Returns:
        True if successful (or shortcut didn't exist), False on error.
    """
    shortcut_path = get_shortcut_path()
    if not shortcut_path:
        return True  # Nothing to disable

    if not shortcut_path.exists():
        logger.debug("Startup shortcut does not exist, nothing to disable")
        return True

    try:
        shortcut_path.unlink()
        logger.info(f"Removed startup shortcut: {shortcut_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove startup shortcut: {e}")
        return False


def toggle_startup() -> bool:
    """Toggle auto-start with Windows.

    Returns:
        New state: True if now enabled, False if now disabled.
    """
    if is_startup_enabled():
        disable_startup()
        return False
    else:
        enable_startup()
        return True
