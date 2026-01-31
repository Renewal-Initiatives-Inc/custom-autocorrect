"""Single instance enforcement using Windows mutex.

Prevents multiple instances of Custom Autocorrect from running
simultaneously, which would cause keystroke duplication and conflicts.

Usage:
    lock = SingleInstanceLock()
    if not lock.acquire():
        # Another instance is running
        show_error_and_exit()

    try:
        # Run application
        ...
    finally:
        lock.release()
"""

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Mutex name must be unique to this application
MUTEX_NAME = "CustomAutocorrect_SingleInstance_Mutex"


class SingleInstanceLock:
    """Manages a system-wide mutex to enforce single instance.

    Uses Windows named mutex via win32event. The mutex is automatically
    released by the OS if the process crashes.
    """

    def __init__(self, mutex_name: str = MUTEX_NAME):
        """Initialize the lock.

        Args:
            mutex_name: Name of the Windows mutex.
        """
        self._mutex_name = mutex_name
        self._mutex_handle: Optional[int] = None
        self._acquired = False

    @property
    def is_acquired(self) -> bool:
        """Check if this instance holds the lock."""
        return self._acquired

    def acquire(self) -> bool:
        """Try to acquire the single instance lock.

        Returns:
            True if lock acquired (we are the only instance),
            False if another instance already has the lock.
        """
        if self._acquired:
            return True

        try:
            import win32event
            import win32api
            import winerror
        except ImportError:
            logger.warning(
                "win32event not available, skipping single instance check"
            )
            # Allow running without check if pywin32 not available
            self._acquired = True
            return True

        try:
            # Try to create a named mutex
            # If it already exists, CreateMutex succeeds but GetLastError
            # returns ERROR_ALREADY_EXISTS
            self._mutex_handle = win32event.CreateMutex(
                None,  # Default security attributes
                True,  # Initially owned by this process
                self._mutex_name
            )

            last_error = win32api.GetLastError()

            if last_error == winerror.ERROR_ALREADY_EXISTS:
                # Another instance has the mutex
                logger.info("Another instance is already running")
                # Close our handle since we don't own it
                if self._mutex_handle:
                    win32api.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None
                return False

            # We successfully created and own the mutex
            self._acquired = True
            logger.debug(f"Acquired single instance lock: {self._mutex_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create mutex: {e}")
            # On error, allow running (fail open)
            self._acquired = True
            return True

    def release(self) -> None:
        """Release the single instance lock."""
        if not self._acquired:
            return

        if self._mutex_handle is not None:
            try:
                import win32api
                win32api.CloseHandle(self._mutex_handle)
                logger.debug("Released single instance lock")
            except Exception as e:
                logger.debug(f"Error releasing mutex: {e}")
            finally:
                self._mutex_handle = None

        self._acquired = False

    def __enter__(self) -> "SingleInstanceLock":
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()


def is_another_instance_running() -> bool:
    """Quick check if another instance is already running.

    This creates a temporary lock, checks, and releases immediately.
    For the main application, use SingleInstanceLock directly.

    Returns:
        True if another instance is running, False otherwise.
    """
    lock = SingleInstanceLock()
    if lock.acquire():
        lock.release()
        return False
    return True


def show_already_running_dialog() -> None:
    """Show a dialog informing user that app is already running."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        messagebox.showwarning(
            "Custom Autocorrect",
            "Custom Autocorrect is already running.\n\n"
            "Look for the pillow icon in your system tray.",
            parent=root
        )

        root.destroy()
    except Exception as e:
        logger.warning(f"Failed to show dialog: {e}")
        # Fall back to console message
        print("Custom Autocorrect is already running.")
        print("Look for the pillow icon in your system tray.")
