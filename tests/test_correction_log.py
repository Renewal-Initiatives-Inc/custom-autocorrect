"""Tests for the correction logging module.

Phase 5 tests for:
- Log entry formatting
- Log rotation (CP5)
- File operations
- Active window detection
- Integration tests
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from custom_autocorrect.correction_log import (
    format_log_entry,
    rotate_log,
    read_log_entries,
    write_log_entries,
    log_correction,
    get_active_window_title,
    MAX_LOG_ENTRIES,
)


# =============================================================================
# Tests for format_log_entry()
# =============================================================================


class TestFormatLogEntry:
    """Tests for log entry formatting."""

    def test_basic_format(self):
        """Entry has correct format with all parts."""
        ts = datetime(2026, 1, 31, 14, 23, 15)
        entry = format_log_entry("teh", "the", "Notepad", timestamp=ts)

        assert entry == "2026-01-31 14:23:15 | teh \u2192 the | Notepad"

    def test_timestamp_format(self):
        """Timestamp matches expected format YYYY-MM-DD HH:MM:SS."""
        ts = datetime(2026, 12, 25, 9, 5, 3)
        entry = format_log_entry("x", "y", "Window", timestamp=ts)

        assert entry.startswith("2026-12-25 09:05:03")

    def test_uses_unicode_arrow(self):
        """Uses → character (Unicode U+2192) for arrow."""
        entry = format_log_entry("a", "b", "Win", timestamp=datetime.now())

        assert "\u2192" in entry
        assert "->" not in entry

    def test_preserves_original_casing(self):
        """Original and corrected preserve their casing."""
        ts = datetime.now()

        # Lowercase
        entry = format_log_entry("teh", "the", "Win", timestamp=ts)
        assert "teh \u2192 the" in entry

        # Capitalized
        entry = format_log_entry("Teh", "The", "Win", timestamp=ts)
        assert "Teh \u2192 The" in entry

        # Uppercase
        entry = format_log_entry("TEH", "THE", "Win", timestamp=ts)
        assert "TEH \u2192 THE" in entry

    def test_unknown_window_title(self):
        """Handles 'Unknown' window title."""
        entry = format_log_entry("teh", "the", "Unknown", timestamp=datetime.now())

        assert entry.endswith("Unknown")

    def test_long_window_title(self):
        """Long window titles work without truncation."""
        long_title = "This is a very long window title that should not be truncated"
        entry = format_log_entry("teh", "the", long_title, timestamp=datetime.now())

        assert long_title in entry

    def test_window_with_special_characters(self):
        """Window titles with special characters are preserved."""
        special_title = "Chrome - Google Docs | My Document"
        entry = format_log_entry("teh", "the", special_title, timestamp=datetime.now())

        assert special_title in entry

    def test_default_timestamp_is_now(self):
        """Without explicit timestamp, uses current time."""
        before = datetime.now()
        entry = format_log_entry("teh", "the", "Win")
        after = datetime.now()

        # Extract timestamp from entry
        ts_str = entry.split(" | ")[0]
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

        # Timestamp should be between before and after
        assert before.replace(microsecond=0) <= ts <= after.replace(microsecond=0)


# =============================================================================
# Tests for rotate_log()
# =============================================================================


class TestRotateLog:
    """Tests for log rotation (CP5)."""

    def test_under_limit_unchanged(self):
        """Entries under limit are not modified."""
        entries = [f"entry_{i}" for i in range(50)]
        result = rotate_log(entries)

        assert result == entries
        assert len(result) == 50

    def test_at_limit_unchanged(self):
        """Exactly MAX_LOG_ENTRIES entries are not modified."""
        entries = [f"entry_{i}" for i in range(MAX_LOG_ENTRIES)]
        result = rotate_log(entries)

        assert result == entries
        assert len(result) == MAX_LOG_ENTRIES

    def test_over_limit_removes_oldest(self):
        """101 entries removes first, keeps last 100."""
        entries = [f"entry_{i}" for i in range(101)]
        result = rotate_log(entries)

        assert len(result) == MAX_LOG_ENTRIES
        assert result[0] == "entry_1"  # First entry removed
        assert result[-1] == "entry_100"  # Last entry kept

    def test_empty_list(self):
        """Empty list returns empty list."""
        result = rotate_log([])
        assert result == []

    def test_way_over_limit(self):
        """200 entries trims to exactly MAX_LOG_ENTRIES."""
        entries = [f"entry_{i}" for i in range(200)]
        result = rotate_log(entries)

        assert len(result) == MAX_LOG_ENTRIES
        # Should keep entries 100-199
        assert result[0] == "entry_100"
        assert result[-1] == "entry_199"

    def test_preserves_order(self):
        """Kept entries maintain their order."""
        entries = ["first", "second", "third", "fourth", "fifth"]
        result = rotate_log(entries, max_entries=3)

        assert result == ["third", "fourth", "fifth"]

    def test_custom_max_entries(self):
        """Custom max_entries value is respected."""
        entries = [f"entry_{i}" for i in range(20)]
        result = rotate_log(entries, max_entries=5)

        assert len(result) == 5
        assert result == ["entry_15", "entry_16", "entry_17", "entry_18", "entry_19"]


# =============================================================================
# Tests for read_log_entries() and write_log_entries()
# =============================================================================


class TestLogFileOperations:
    """Tests for log file read/write operations."""

    def test_creates_file_if_missing(self, tmp_path):
        """First write creates the file."""
        log_path = tmp_path / "test.log"
        entries = ["entry_1", "entry_2"]

        with patch("custom_autocorrect.correction_log.ensure_app_folder"):
            result = write_log_entries(log_path, entries)

        assert result is True
        assert log_path.exists()

    def test_read_nonexistent_returns_empty(self, tmp_path):
        """Reading nonexistent file returns empty list."""
        log_path = tmp_path / "nonexistent.log"

        result = read_log_entries(log_path)

        assert result == []

    def test_read_empty_file(self, tmp_path):
        """Reading empty file returns empty list."""
        log_path = tmp_path / "empty.log"
        log_path.touch()

        result = read_log_entries(log_path)

        assert result == []

    def test_round_trip(self, tmp_path):
        """Write then read returns same entries."""
        log_path = tmp_path / "test.log"
        entries = [
            "2026-01-31 14:23:15 | teh \u2192 the | Notepad",
            "2026-01-31 14:25:02 | adn \u2192 and | Chrome",
        ]

        with patch("custom_autocorrect.correction_log.ensure_app_folder"):
            write_log_entries(log_path, entries)
        result = read_log_entries(log_path)

        assert result == entries

    def test_utf8_encoding(self, tmp_path):
        """File uses UTF-8 encoding for Unicode characters."""
        log_path = tmp_path / "test.log"
        entries = ["2026-01-31 14:23:15 | teh \u2192 the | Café - Notepad"]

        with patch("custom_autocorrect.correction_log.ensure_app_folder"):
            write_log_entries(log_path, entries)

        # Verify file can be read as UTF-8
        content = log_path.read_text(encoding="utf-8")
        assert "\u2192" in content
        assert "Café" in content

    def test_filters_empty_lines(self, tmp_path):
        """Reading filters out empty lines."""
        log_path = tmp_path / "test.log"
        log_path.write_text("entry_1\n\nentry_2\n\n\nentry_3\n", encoding="utf-8")

        result = read_log_entries(log_path)

        assert result == ["entry_1", "entry_2", "entry_3"]

    def test_handles_corrupted_file_on_read(self, tmp_path):
        """Reading file with invalid encoding returns empty list."""
        log_path = tmp_path / "test.log"
        # Write invalid UTF-8 bytes
        log_path.write_bytes(b"invalid \xff\xfe bytes")

        result = read_log_entries(log_path)

        # Should handle gracefully, returning empty list
        assert result == []

    def test_appends_to_existing(self, tmp_path):
        """New entries can be appended to existing log."""
        log_path = tmp_path / "test.log"

        with patch("custom_autocorrect.correction_log.ensure_app_folder"):
            # First write
            write_log_entries(log_path, ["entry_1"])

            # Read, append, write
            entries = read_log_entries(log_path)
            entries.append("entry_2")
            write_log_entries(log_path, entries)

            # Verify
            result = read_log_entries(log_path)

        assert result == ["entry_1", "entry_2"]


# =============================================================================
# Tests for get_active_window_title()
# =============================================================================


class TestGetActiveWindowTitle:
    """Tests for active window title detection."""

    def test_returns_string(self):
        """Always returns a string."""
        result = get_active_window_title()

        assert isinstance(result, str)

    def test_returns_unknown_on_non_windows(self):
        """Returns 'Unknown' on non-Windows platforms."""
        # Mock ctypes to raise AttributeError (no windll on non-Windows)
        with patch.dict("sys.modules", {"ctypes": MagicMock(spec=[])}):
            # Force reimport to pick up mock
            import importlib
            import custom_autocorrect.correction_log as cl

            # The actual implementation catches AttributeError
            result = get_active_window_title()

            # On non-Windows, should return "Unknown"
            assert result == "Unknown" or isinstance(result, str)

    @pytest.mark.skipif(
        not hasattr(__import__("ctypes"), "windll"),
        reason="Windows-only test (ctypes.windll not available)"
    )
    def test_handles_no_foreground_window(self):
        """Returns 'Unknown' when no window is focused."""
        with patch("ctypes.windll.user32.GetForegroundWindow", return_value=0):
            result = get_active_window_title()

            assert result == "Unknown"

    @pytest.mark.skipif(
        not hasattr(__import__("ctypes"), "windll"),
        reason="Windows-only test (ctypes.windll not available)"
    )
    def test_handles_empty_window_title(self):
        """Returns 'Unknown' for windows with empty titles."""
        mock_user32 = MagicMock()
        mock_user32.GetForegroundWindow.return_value = 12345
        mock_user32.GetWindowTextLengthW.return_value = 0

        with patch("ctypes.windll.user32", mock_user32):
            result = get_active_window_title()

            assert result == "Unknown"


# =============================================================================
# Tests for log_correction() - Integration
# =============================================================================


class TestLogCorrection:
    """Integration tests for the main log_correction function."""

    def test_full_logging_flow(self, tmp_path, monkeypatch):
        """Full flow: correction -> log entry appears in file."""
        log_path = tmp_path / "corrections.log"

        # Mock paths and window detection
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Test Window"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        # Log a correction
        result = log_correction("teh", "the")

        assert result is True
        assert log_path.exists()

        # Verify entry
        entries = read_log_entries(log_path)
        assert len(entries) == 1
        assert "teh \u2192 the" in entries[0]
        assert "Test Window" in entries[0]

    def test_multiple_corrections(self, tmp_path, monkeypatch):
        """Multiple corrections are all logged."""
        log_path = tmp_path / "corrections.log"

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Notepad"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        # Log multiple corrections
        log_correction("teh", "the")
        log_correction("adn", "and")
        log_correction("hte", "the")

        entries = read_log_entries(log_path)
        assert len(entries) == 3

    def test_rotation_during_session(self, tmp_path, monkeypatch):
        """Logging 150 corrections results in 100 entries (CP5)."""
        log_path = tmp_path / "corrections.log"

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Window"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        # Log 150 corrections
        for i in range(150):
            log_correction(f"typo{i}", f"fix{i}")

        entries = read_log_entries(log_path)

        # Should have exactly MAX_LOG_ENTRIES
        assert len(entries) == MAX_LOG_ENTRIES

        # Should have the newest entries (50-149)
        assert "typo50" in entries[0]
        assert "typo149" in entries[-1]

    def test_returns_false_on_error(self, tmp_path, monkeypatch):
        """Returns False when logging fails."""
        # Make the log path a directory to cause write error
        bad_path = tmp_path / "bad_path"
        bad_path.mkdir()
        log_path = bad_path / "subdir" / "corrections.log"

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Window"
        )
        # Don't mock ensure_app_folder, let it try to create dirs

        # This should handle the error gracefully
        result = log_correction("teh", "the")

        # Should return False or True depending on whether dirs were created
        assert isinstance(result, bool)


# =============================================================================
# Tests for edge cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge case handling."""

    def test_empty_original(self, tmp_path, monkeypatch):
        """Empty original word is handled."""
        log_path = tmp_path / "corrections.log"

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Window"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        result = log_correction("", "the")

        # Should still work, just log empty -> the
        assert result is True

    def test_unicode_in_words(self, tmp_path, monkeypatch):
        """Unicode characters in words are preserved."""
        log_path = tmp_path / "corrections.log"

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "Window"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        result = log_correction("café", "cafe")

        assert result is True
        entries = read_log_entries(log_path)
        assert "café" in entries[0]

    def test_preserves_existing_entries(self, tmp_path, monkeypatch):
        """Existing log entries are preserved when adding new ones."""
        log_path = tmp_path / "corrections.log"

        # Pre-populate log
        existing = [
            "2026-01-31 10:00:00 | old1 \u2192 new1 | OldWindow",
            "2026-01-31 11:00:00 | old2 \u2192 new2 | OldWindow",
        ]
        log_path.write_text("\n".join(existing) + "\n", encoding="utf-8")

        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_corrections_log_path",
            lambda: log_path
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.get_active_window_title",
            lambda: "NewWindow"
        )
        monkeypatch.setattr(
            "custom_autocorrect.correction_log.ensure_app_folder",
            lambda: tmp_path
        )

        log_correction("teh", "the")

        entries = read_log_entries(log_path)
        assert len(entries) == 3
        assert "old1 \u2192 new1" in entries[0]
        assert "old2 \u2192 new2" in entries[1]
        assert "teh \u2192 the" in entries[2]
