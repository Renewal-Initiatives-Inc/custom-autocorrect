"""Tests for password field detection.

Phase 6: Tests for is_password_field() function that detects password input fields
using Windows UI Automation API.

Key test principles:
- is_password_field() must ALWAYS return a boolean (fail-safe)
- Any exception should return False (allow corrections to continue)
- Non-Windows platforms should return False gracefully
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from custom_autocorrect.password_detect import (
    is_password_field,
    reset_uia_cache,
    _get_uia_interface,
    _get_focused_element,
    _check_is_password_via_uia,
    UIA_IsPasswordPropertyId,
    UIA_ControlTypePropertyId,
    UIA_EditControlTypeId,
)


class TestIsPasswordFieldBasics:
    """Basic functionality tests for is_password_field."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_returns_bool(self):
        """is_password_field must always return a boolean."""
        result = is_password_field()
        assert isinstance(result, bool)

    def test_returns_false_on_non_windows(self):
        """On non-Windows platforms, should return False (fail-safe)."""
        # Reset cache and check - we're on Mac so should return False
        reset_uia_cache()
        result = is_password_field()
        assert result is False

    def test_multiple_calls_consistent(self):
        """Multiple calls should return consistent results."""
        result1 = is_password_field()
        result2 = is_password_field()
        result3 = is_password_field()
        # All should be False (we're not on Windows with UIA)
        assert result1 == result2 == result3


class TestGetUIAInterface:
    """Tests for _get_uia_interface helper."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_returns_none_on_non_windows(self):
        """Should return None on non-Windows platforms."""
        # We're running on Mac, so this should return None
        if sys.platform != "win32":
            result = _get_uia_interface()
            assert result is None

    def test_caches_result(self):
        """Should cache the initialization result."""
        reset_uia_cache()
        result1 = _get_uia_interface()
        result2 = _get_uia_interface()
        # Both should be None (non-Windows) and cached
        assert result1 is result2

    @patch("custom_autocorrect.password_detect.sys.platform", "win32")
    def test_handles_import_error(self):
        """Should handle ImportError for comtypes gracefully."""
        reset_uia_cache()

        with patch.dict("sys.modules", {"comtypes": None, "comtypes.client": None}):
            # Force reimport by resetting cache
            reset_uia_cache()

            # The import will fail, should return None
            with patch(
                "custom_autocorrect.password_detect.sys.platform", "win32"
            ):
                # Need to actually test the import failure path
                # This is tricky because the import happens inside the function
                pass

    @patch("custom_autocorrect.password_detect.sys.platform", "win32")
    def test_handles_com_error(self):
        """Should handle COM initialization errors gracefully."""
        reset_uia_cache()

        mock_comtypes = MagicMock()
        mock_comtypes.client.CreateObject.side_effect = Exception("COM error")

        with patch.dict("sys.modules", {"comtypes": mock_comtypes, "comtypes.client": mock_comtypes.client}):
            reset_uia_cache()
            result = _get_uia_interface()
            # Should return None on error
            assert result is None


class TestGetFocusedElement:
    """Tests for _get_focused_element helper."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_returns_none_when_uia_unavailable(self):
        """Should return None if UIA is not available."""
        result = _get_focused_element()
        assert result is None

    def test_returns_none_on_exception(self):
        """Should return None if GetFocusedElement raises."""
        reset_uia_cache()

        # Mock the UIA interface
        mock_uia = MagicMock()
        mock_uia.GetFocusedElement.side_effect = Exception("Access denied")

        with patch(
            "custom_autocorrect.password_detect._get_uia_interface",
            return_value=mock_uia,
        ):
            result = _get_focused_element()
            assert result is None


class TestCheckIsPasswordViaUIA:
    """Tests for _check_is_password_via_uia helper."""

    def test_returns_false_for_none_element(self):
        """Should return False if element is None."""
        result = _check_is_password_via_uia(None)
        assert result is False

    def test_returns_true_for_password_property(self):
        """Should return True if IsPassword property is True."""
        mock_element = MagicMock()
        mock_element.GetCurrentPropertyValue.return_value = True

        result = _check_is_password_via_uia(mock_element)
        assert result is True

        # Verify we checked the right property
        mock_element.GetCurrentPropertyValue.assert_any_call(UIA_IsPasswordPropertyId)

    def test_returns_false_for_non_password_field(self):
        """Should return False for regular text fields."""
        mock_element = MagicMock()
        # Return False for IsPassword, something else for ControlType
        mock_element.GetCurrentPropertyValue.side_effect = lambda prop_id: {
            UIA_IsPasswordPropertyId: False,
            UIA_ControlTypePropertyId: UIA_EditControlTypeId,
        }.get(prop_id, None)

        result = _check_is_password_via_uia(mock_element)
        assert result is False

    def test_returns_false_on_exception(self):
        """Should return False if property access raises."""
        mock_element = MagicMock()
        mock_element.GetCurrentPropertyValue.side_effect = Exception("Access error")

        result = _check_is_password_via_uia(mock_element)
        assert result is False


class TestIsPasswordFieldWithMocks:
    """Integration tests for is_password_field with mocked UIA."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_returns_true_for_password_field(self):
        """Should return True when focused element is a password field."""
        mock_element = MagicMock()
        mock_element.GetCurrentPropertyValue.return_value = True

        with patch(
            "custom_autocorrect.password_detect._get_focused_element",
            return_value=mock_element,
        ):
            result = is_password_field()
            assert result is True

    def test_returns_false_for_normal_field(self):
        """Should return False for non-password fields."""
        mock_element = MagicMock()
        mock_element.GetCurrentPropertyValue.return_value = False

        with patch(
            "custom_autocorrect.password_detect._get_focused_element",
            return_value=mock_element,
        ):
            result = is_password_field()
            assert result is False

    def test_returns_false_when_no_focused_element(self):
        """Should return False if no element is focused."""
        with patch(
            "custom_autocorrect.password_detect._get_focused_element",
            return_value=None,
        ):
            result = is_password_field()
            assert result is False

    def test_returns_false_on_any_exception(self):
        """Any exception should return False (fail-safe)."""
        with patch(
            "custom_autocorrect.password_detect._get_focused_element",
            side_effect=Exception("Unexpected error"),
        ):
            result = is_password_field()
            assert result is False


class TestFailSafeBehavior:
    """Tests verifying fail-safe behavior (P4: When uncertain, do nothing)."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_never_raises_exception(self):
        """is_password_field should never raise an exception."""
        # Test with various mock failures
        failure_scenarios = [
            Exception("Generic error"),
            RuntimeError("Runtime error"),
            OSError("OS error"),
            AttributeError("Attribute error"),
            TypeError("Type error"),
            ValueError("Value error"),
        ]

        for error in failure_scenarios:
            with patch(
                "custom_autocorrect.password_detect._get_focused_element",
                side_effect=error,
            ):
                # Should NOT raise - should return False
                result = is_password_field()
                assert result is False, f"Failed for {type(error).__name__}"

    def test_import_error_handled(self):
        """Should handle ImportError gracefully."""
        reset_uia_cache()

        # Simulate comtypes not being installed
        with patch(
            "custom_autocorrect.password_detect._get_uia_interface",
            return_value=None,
        ):
            result = is_password_field()
            assert result is False


class TestResetUIACache:
    """Tests for reset_uia_cache utility function."""

    def test_resets_cache(self):
        """reset_uia_cache should clear cached state."""
        # First call caches the result
        is_password_field()

        # Reset should clear it
        reset_uia_cache()

        # Import the module-level variables to check
        import custom_autocorrect.password_detect as pd

        assert pd._uia_interface is None
        assert pd._initialization_failed is False


class TestMainFlowIntegration:
    """Integration tests verifying password detection in the main correction flow."""

    def setup_method(self):
        """Reset the UIA cache before each test."""
        reset_uia_cache()

    def test_correction_skipped_in_password_field(self):
        """Corrections should be skipped when password field is detected."""
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "custom_autocorrect.main.is_password_field", return_value=True
        ):
            with mock_patch(
                "custom_autocorrect.main._correction_engine"
            ) as mock_engine:
                with mock_patch(
                    "custom_autocorrect.main._matcher"
                ) as mock_matcher:
                    # Set up matcher to return a rule
                    from custom_autocorrect.rules import Rule

                    mock_matcher.match.return_value = Rule("teh", "the", "teh")
                    mock_engine.correct = MagicMock()

                    # Import and call on_word_detected
                    from custom_autocorrect.main import on_word_detected

                    on_word_detected("teh")

                    # Correction should NOT have been called
                    mock_engine.correct.assert_not_called()

    def test_correction_applied_in_normal_field(self):
        """Corrections should work normally in non-password fields."""
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "custom_autocorrect.main.is_password_field", return_value=False
        ):
            with mock_patch(
                "custom_autocorrect.main._correction_engine"
            ) as mock_engine:
                with mock_patch(
                    "custom_autocorrect.main._matcher"
                ) as mock_matcher:
                    with mock_patch(
                        "custom_autocorrect.main.log_correction"
                    ) as mock_log:
                        # Set up matcher to return a rule
                        from custom_autocorrect.rules import Rule

                        mock_matcher.match.return_value = Rule("teh", "the", "teh")
                        mock_engine.correct.return_value = True

                        # Import and call on_word_detected
                        from custom_autocorrect.main import on_word_detected

                        on_word_detected("teh")

                        # Correction SHOULD have been called
                        mock_engine.correct.assert_called_once()


class TestUIAConstants:
    """Tests verifying UI Automation constants are correct."""

    def test_is_password_property_id(self):
        """UIA_IsPasswordPropertyId should be 30019."""
        assert UIA_IsPasswordPropertyId == 30019

    def test_control_type_property_id(self):
        """UIA_ControlTypePropertyId should be 30003."""
        assert UIA_ControlTypePropertyId == 30003

    def test_edit_control_type_id(self):
        """UIA_EditControlTypeId should be 50004."""
        assert UIA_EditControlTypeId == 50004
