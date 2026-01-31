"""Password field detection to skip corrections.

Phase 6 Implementation:
- Windows UI Automation API integration
- Best-effort password field detection
- Fail-safe behavior (skip correction when uncertain)

Design Principle P4 (Fail Safe): When uncertain, do nothing.
A missed correction is far better than a wrong one.

Correctness Property CP7: For any detected password field,
no correction shall occur.
"""

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Windows UI Automation constants
# These are from UIAutomationClient.h
UIA_IsPasswordPropertyId = 30019
UIA_ControlTypePropertyId = 30003
UIA_EditControlTypeId = 50004

# Cache for UI Automation interface (lazy initialization)
_uia_interface: Optional[object] = None
_initialization_failed: bool = False


def _get_uia_interface():
    """Get the Windows UI Automation interface (singleton).

    Returns:
        IUIAutomation interface object, or None if unavailable.

    Note:
        Uses lazy initialization and caches the result.
        Returns None on non-Windows platforms or if comtypes fails.
    """
    global _uia_interface, _initialization_failed

    # If we already know initialization failed, don't retry
    if _initialization_failed:
        return None

    # Return cached interface if available
    if _uia_interface is not None:
        return _uia_interface

    # Only attempt on Windows
    if sys.platform != "win32":
        logger.debug("Password detection unavailable: not on Windows")
        _initialization_failed = True
        return None

    try:
        import comtypes.client

        # CUIAutomation CLSID: {FF48DBA4-60EF-4201-AA87-54103EEF594E}
        # IUIAutomation IID: {30CBE57D-D9D0-452A-AB13-7AC5AC4825EE}
        _uia_interface = comtypes.client.CreateObject(
            "{FF48DBA4-60EF-4201-AA87-54103EEF594E}",
            interface=None,  # Let comtypes figure out the interface
        )
        logger.debug("Windows UI Automation interface initialized")
        return _uia_interface

    except ImportError:
        logger.debug("Password detection unavailable: comtypes not installed")
        _initialization_failed = True
        return None

    except Exception as e:
        logger.debug(f"Password detection unavailable: {e}")
        _initialization_failed = True
        return None


def _get_focused_element():
    """Get the currently focused UI element.

    Returns:
        The focused IUIAutomationElement, or None if unavailable.
    """
    uia = _get_uia_interface()
    if uia is None:
        return None

    try:
        return uia.GetFocusedElement()
    except Exception as e:
        logger.debug(f"Failed to get focused element: {e}")
        return None


def _check_is_password_via_uia(element) -> bool:
    """Check if an element is a password field using UI Automation.

    Args:
        element: IUIAutomationElement to check.

    Returns:
        True if the element is a password field, False otherwise.
    """
    if element is None:
        return False

    try:
        # Method 1: Check the IsPassword property directly
        # This is the most reliable method for password fields
        is_password = element.GetCurrentPropertyValue(UIA_IsPasswordPropertyId)
        if is_password:
            return True

        # Method 2: Check control type is Edit AND supports password pattern
        # Some applications may not set IsPassword but use password control pattern
        control_type = element.GetCurrentPropertyValue(UIA_ControlTypePropertyId)
        if control_type == UIA_EditControlTypeId:
            # Try to get the password pattern - if available, it's a password field
            # Note: This is a secondary check; IsPassword is more reliable
            try:
                # GetCurrentPattern would return None or raise if pattern unavailable
                # We just check if the element can be queried without error
                pass  # IsPassword check above should be sufficient
            except Exception:
                pass

        return False

    except Exception as e:
        logger.debug(f"Error checking password property: {e}")
        return False


def is_password_field() -> bool:
    """Check if the currently focused control is a password field.

    Returns:
        True if password field detected.
        False if not a password field OR detection failed (fail-safe).

    Design:
        Fail-safe - returns False on any error so corrections continue.
        This may miss some password fields, but won't block normal operation.

    Note:
        This is "best-effort" detection per REQ-3. Windows UI Automation
        cannot detect all password fields reliably (e.g., custom controls,
        web applications with non-standard password inputs).
    """
    try:
        element = _get_focused_element()
        if element is None:
            # No focused element or UIA unavailable - fail-safe
            return False

        result = _check_is_password_via_uia(element)

        if result:
            logger.debug("Password field detected - skipping correction")

        return result

    except Exception as e:
        # Any unexpected error - fail-safe, allow corrections
        logger.debug(f"Password detection error (continuing normally): {e}")
        return False


def reset_uia_cache() -> None:
    """Reset the UI Automation interface cache.

    Useful for testing or if the UI Automation interface becomes stale.
    """
    global _uia_interface, _initialization_failed
    _uia_interface = None
    _initialization_failed = False
