"""Tests for the hotkey module.

Phase 9 tests covering:
- Rule validation
- File appending
- AddRuleHotkey class
- Dialog functionality (mocked)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import threading

from custom_autocorrect.hotkey import (
    append_rule_to_file,
    validate_rule_input,
    show_confirmation,
    KEYBOARD_AVAILABLE,
)


class TestValidateRuleInput:
    """Tests for validate_rule_input function."""

    def test_valid_input_returns_none(self):
        """Valid typo and correction returns None (no error)."""
        assert validate_rule_input("teh", "the") is None

    def test_valid_input_with_whitespace(self):
        """Valid input with surrounding whitespace."""
        assert validate_rule_input("  teh  ", "  the  ") is None

    def test_empty_typo_returns_error(self):
        """Empty typo returns error message."""
        error = validate_rule_input("", "the")
        assert error is not None
        assert "empty" in error.lower()

    def test_whitespace_typo_returns_error(self):
        """Whitespace-only typo returns error message."""
        error = validate_rule_input("   ", "the")
        assert error is not None
        assert "empty" in error.lower()

    def test_empty_correction_returns_error(self):
        """Empty correction returns error message."""
        error = validate_rule_input("teh", "")
        assert error is not None
        assert "empty" in error.lower()

    def test_whitespace_correction_returns_error(self):
        """Whitespace-only correction returns error message."""
        error = validate_rule_input("teh", "   ")
        assert error is not None
        assert "empty" in error.lower()

    def test_same_typo_correction_returns_error(self):
        """Typo equals correction returns error."""
        error = validate_rule_input("same", "same")
        assert error is not None
        assert "same" in error.lower()

    def test_same_typo_correction_case_insensitive(self):
        """Typo equals correction (different case) returns error."""
        error = validate_rule_input("Same", "SAME")
        assert error is not None
        assert "same" in error.lower()

    def test_same_typo_correction_mixed_case(self):
        """Mixed case same word returns error."""
        error = validate_rule_input("SaMe", "sAmE")
        assert error is not None


class TestAppendRuleToFile:
    """Tests for append_rule_to_file function."""

    def test_append_to_empty_file(self, tmp_path):
        """Appending to empty file creates rule."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("", encoding="utf-8")

        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert "teh=the" in content

    def test_append_to_existing_file_with_newline(self, tmp_path):
        """Appending to file ending with newline."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("adn=and\n", encoding="utf-8")

        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert content == "adn=and\nteh=the\n"

    def test_append_to_existing_file_without_newline(self, tmp_path):
        """Appending to file not ending with newline adds one."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("adn=and", encoding="utf-8")

        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert content == "adn=and\nteh=the\n"

    def test_append_to_nonexistent_file(self, tmp_path):
        """Appending to nonexistent file creates it."""
        rules_file = tmp_path / "rules.txt"
        assert not rules_file.exists()

        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is True
        assert rules_file.exists()
        content = rules_file.read_text(encoding="utf-8")
        assert "teh=the" in content

    def test_append_preserves_existing_rules(self, tmp_path):
        """Appending preserves all existing rules."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("# Header\nadn=and\nhte=the\n", encoding="utf-8")

        result = append_rule_to_file("taht", "that", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert "# Header" in content
        assert "adn=and" in content
        assert "hte=the" in content
        assert "taht=that" in content

    def test_append_unicode_characters(self, tmp_path):
        """Unicode characters are preserved."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("", encoding="utf-8")

        result = append_rule_to_file("cafe", "café", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert "cafe=café" in content

    def test_append_handles_permission_error(self, tmp_path):
        """Permission errors return False."""
        rules_file = tmp_path / "readonly" / "rules.txt"
        # Don't create the directory - this will cause an error

        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is False


class TestAddRuleHotkey:
    """Tests for AddRuleHotkey class."""

    def test_init_stores_callback(self):
        """Should store the callback."""
        with patch.dict("sys.modules", {"keyboard": MagicMock()}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                callback = MagicMock()
                hotkey = AddRuleHotkey(on_rule_added=callback)
                assert hotkey._on_rule_added is callback
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_init_not_registered(self):
        """Should initialize as not registered."""
        with patch.dict("sys.modules", {"keyboard": MagicMock()}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                assert hotkey.is_registered is False
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_register_calls_add_hotkey(self):
        """Register should call keyboard.add_hotkey."""
        mock_keyboard = MagicMock()
        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.register()

                mock_keyboard.add_hotkey.assert_called_once()
                call_args = mock_keyboard.add_hotkey.call_args
                assert "win+shift+a" in call_args[0][0].lower()
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_register_sets_registered_flag(self):
        """Register should set is_registered to True."""
        mock_keyboard = MagicMock()
        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.register()

                assert hotkey.is_registered is True
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_register_twice_is_safe(self):
        """Registering twice should not create duplicate hotkeys."""
        mock_keyboard = MagicMock()
        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.register()
                hotkey.register()

                # Should only be called once
                assert mock_keyboard.add_hotkey.call_count == 1
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_unregister_calls_remove_hotkey(self):
        """Unregister should call keyboard.remove_hotkey."""
        mock_keyboard = MagicMock()
        mock_keyboard.add_hotkey.return_value = "hotkey_id"

        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.register()
                hotkey.unregister()

                mock_keyboard.remove_hotkey.assert_called_once_with("hotkey_id")
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_unregister_sets_registered_flag(self):
        """Unregister should set is_registered to False."""
        mock_keyboard = MagicMock()
        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.register()
                hotkey.unregister()

                assert hotkey.is_registered is False
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_unregister_when_not_registered(self):
        """Unregistering when not registered should be safe."""
        mock_keyboard = MagicMock()
        with patch.dict("sys.modules", {"keyboard": mock_keyboard}):
            import custom_autocorrect.hotkey as hotkey_module

            original_available = hotkey_module.KEYBOARD_AVAILABLE
            hotkey_module.KEYBOARD_AVAILABLE = True
            hotkey_module.keyboard = mock_keyboard

            try:
                from custom_autocorrect.hotkey import AddRuleHotkey

                hotkey = AddRuleHotkey()
                hotkey.unregister()  # Should not raise

                mock_keyboard.remove_hotkey.assert_not_called()
            finally:
                hotkey_module.KEYBOARD_AVAILABLE = original_available

    def test_init_raises_without_keyboard(self):
        """Should raise ImportError if keyboard not available."""
        import custom_autocorrect.hotkey as hotkey_module

        original_available = hotkey_module.KEYBOARD_AVAILABLE
        hotkey_module.KEYBOARD_AVAILABLE = False

        try:
            from custom_autocorrect.hotkey import AddRuleHotkey

            with pytest.raises(ImportError):
                AddRuleHotkey()
        finally:
            hotkey_module.KEYBOARD_AVAILABLE = original_available


class TestShowConfirmation:
    """Tests for show_confirmation function."""

    def test_confirmation_runs_in_thread(self):
        """Confirmation should run in a separate thread."""
        with patch("custom_autocorrect.hotkey.threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            show_confirmation("teh", "the")

            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()


class TestHotkeyIntegration:
    """Integration tests for the hotkey flow."""

    def test_hotkey_callback_appends_rule(self, tmp_path):
        """Hotkey callback should append rule to file."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("", encoding="utf-8")

        # Manually test append_rule_to_file since we can't trigger dialog
        result = append_rule_to_file("teh", "the", rules_path=rules_file)

        assert result is True
        content = rules_file.read_text(encoding="utf-8")
        assert "teh=the" in content

    def test_appended_rule_is_valid_format(self, tmp_path):
        """Appended rule should be valid for rule parser."""
        from custom_autocorrect.rules import RuleParser

        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("# existing\nadn=and\n", encoding="utf-8")

        append_rule_to_file("teh", "the", rules_path=rules_file)

        # Parse the file with RuleParser
        rules, errors = RuleParser.parse_file(rules_file)

        assert len(errors) == 0
        assert "teh" in rules
        assert "adn" in rules
        assert rules["teh"].correction == "the"

    def test_appended_rule_triggers_reload(self, tmp_path):
        """Appended rule should trigger file watcher reload."""
        from custom_autocorrect.rules import RuleMatcher

        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("adn=and\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()
        assert matcher.rule_count == 1

        # Append new rule
        append_rule_to_file("teh", "the", rules_path=rules_file)

        # Reload should pick up new rule
        matcher.reload_if_changed()
        assert matcher.rule_count == 2
        assert matcher.match("teh") is not None
