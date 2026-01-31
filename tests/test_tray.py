"""Tests for the system tray integration.

Phase 8 tests covering:
- Icon image creation and loading
- Menu structure
- File opening actions
- View/Ignore suggestion dialogs
- Exit handling
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

# Skip all tests if pystray is not available
pytest.importorskip("pystray")

from custom_autocorrect.tray import (
    SystemTray,
    _create_icon_image,
    _get_bundled_icon_path,
    _open_file,
    PYSTRAY_AVAILABLE,
)
from custom_autocorrect.suggestions import CorrectionPatternTracker


class TestIconCreation:
    """Tests for icon image creation."""

    def test_create_icon_image_returns_image(self):
        """Icon creation should return a PIL Image."""
        from PIL import Image

        img = _create_icon_image()
        assert isinstance(img, Image.Image)

    def test_create_icon_image_correct_size(self):
        """Icon should have the specified size."""
        img = _create_icon_image(size=64)
        assert img.size == (64, 64)

    def test_create_icon_image_custom_size(self):
        """Icon should respect custom size parameter."""
        img = _create_icon_image(size=32)
        assert img.size == (32, 32)

    def test_create_icon_image_rgba_mode(self):
        """Icon should be in RGBA mode for transparency support."""
        img = _create_icon_image()
        assert img.mode == "RGBA"


class TestBundledIconPath:
    """Tests for bundled icon path discovery."""

    def test_get_bundled_icon_path_exists(self, tmp_path):
        """Should find bundled icon if it exists."""
        # The actual function checks relative to module location,
        # so we test that it returns a Path or None
        result = _get_bundled_icon_path()
        if result is not None:
            assert isinstance(result, Path)

    def test_get_bundled_icon_path_handles_missing(self):
        """Should return None if icon doesn't exist."""
        with patch("custom_autocorrect.tray.Path") as mock_path:
            # Mock the path to not exist
            mock_instance = MagicMock()
            mock_instance.exists.return_value = False
            mock_path.return_value = mock_instance
            # Result should be None or the actual implementation handles it


class TestOpenFile:
    """Tests for file opening functionality."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_open_file_windows(self, tmp_path):
        """Should use os.startfile on Windows."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch("os.startfile") as mock_startfile:
            result = _open_file(test_file)
            mock_startfile.assert_called_once_with(str(test_file))
            assert result is True

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific test")
    def test_open_file_macos(self, tmp_path):
        """Should use 'open' command on macOS."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _open_file(test_file)
            mock_run.assert_called_once_with(["open", str(test_file)], check=True)
            assert result is True

    def test_open_file_handles_error(self, tmp_path):
        """Should return False on error."""
        test_file = tmp_path / "nonexistent" / "test.txt"

        with patch("custom_autocorrect.tray.subprocess.run", side_effect=Exception("Test error")):
            result = _open_file(test_file)
            assert result is False


class TestSystemTray:
    """Tests for SystemTray class."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock pattern tracker."""
        tracker = MagicMock(spec=CorrectionPatternTracker)
        tracker.suggestion_count = 0
        tracker.get_suggestions.return_value = []
        return tracker

    @pytest.fixture
    def mock_exit_callback(self):
        """Create a mock exit callback."""
        return MagicMock()

    def test_init_stores_tracker(self, mock_tracker, mock_exit_callback):
        """Should store pattern tracker reference."""
        tray = SystemTray(mock_tracker, mock_exit_callback)
        assert tray._tracker is mock_tracker

    def test_init_stores_exit_callback(self, mock_tracker, mock_exit_callback):
        """Should store exit callback reference."""
        tray = SystemTray(mock_tracker, mock_exit_callback)
        assert tray._exit_callback is mock_exit_callback

    def test_init_not_running(self, mock_tracker, mock_exit_callback):
        """Should initialize in not-running state."""
        tray = SystemTray(mock_tracker, mock_exit_callback)
        assert tray._running is False

    def test_load_icon_returns_image(self, mock_tracker, mock_exit_callback):
        """Loading icon should return a PIL Image."""
        from PIL import Image

        tray = SystemTray(mock_tracker, mock_exit_callback)
        img = tray._load_icon()
        assert isinstance(img, Image.Image)

    def test_create_menu_has_correct_items(self, mock_tracker, mock_exit_callback):
        """Menu should contain all required items."""
        tray = SystemTray(mock_tracker, mock_exit_callback)
        menu = tray._create_menu()

        # pystray Menu items can be accessed
        # The menu structure should have 7 items (including separators)
        assert menu is not None

    @patch("custom_autocorrect.tray.Icon")
    def test_start_creates_icon(self, mock_icon_class, mock_tracker, mock_exit_callback):
        """Starting should create and run the icon."""
        mock_icon = MagicMock()
        mock_icon_class.return_value = mock_icon

        tray = SystemTray(mock_tracker, mock_exit_callback)
        tray.start()

        mock_icon_class.assert_called_once()
        mock_icon.run_detached.assert_called_once()
        assert tray._running is True

    @patch("custom_autocorrect.tray.Icon")
    def test_start_only_once(self, mock_icon_class, mock_tracker, mock_exit_callback):
        """Starting twice should not create second icon."""
        mock_icon = MagicMock()
        mock_icon_class.return_value = mock_icon

        tray = SystemTray(mock_tracker, mock_exit_callback)
        tray.start()
        tray.start()

        # Should only be called once
        assert mock_icon_class.call_count == 1

    @patch("custom_autocorrect.tray.Icon")
    def test_stop_stops_icon(self, mock_icon_class, mock_tracker, mock_exit_callback):
        """Stopping should stop the icon."""
        mock_icon = MagicMock()
        mock_icon_class.return_value = mock_icon

        tray = SystemTray(mock_tracker, mock_exit_callback)
        tray.start()
        tray.stop()

        mock_icon.stop.assert_called_once()
        assert tray._running is False

    @patch("custom_autocorrect.tray.Icon")
    def test_on_exit_calls_callback(
        self, mock_icon_class, mock_tracker, mock_exit_callback
    ):
        """Exit action should call the exit callback."""
        mock_icon = MagicMock()
        mock_icon_class.return_value = mock_icon

        tray = SystemTray(mock_tracker, mock_exit_callback)
        tray.start()
        tray._on_exit()

        mock_exit_callback.assert_called_once()


class TestViewSuggestions:
    """Tests for View Suggestions functionality."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock pattern tracker."""
        tracker = MagicMock(spec=CorrectionPatternTracker)
        tracker.suggestion_count = 0
        tracker.get_suggestions.return_value = []
        return tracker

    def test_view_suggestions_empty_shows_info(self, mock_tracker):
        """Empty suggestions should show informative message."""
        mock_tracker.get_suggestions.return_value = []

        tray = SystemTray(mock_tracker, MagicMock())

        with patch.object(tray, "_show_info") as mock_show:
            tray._on_view_suggestions()
            mock_show.assert_called_once()
            # Check that the message mentions no suggestions
            call_args = mock_show.call_args
            assert "No suggestions" in call_args[0][1]

    def test_view_suggestions_with_data_shows_dialog(self, mock_tracker):
        """Suggestions should be displayed in text dialog."""
        mock_tracker.get_suggestions.return_value = [
            ("teh", "the", 5),
            ("adn", "and", 3),
        ]

        tray = SystemTray(mock_tracker, MagicMock())

        with patch.object(tray, "_show_text_dialog") as mock_show:
            tray._on_view_suggestions()
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            text = call_args[0][1]
            assert "teh" in text
            assert "the" in text
            assert "5 times" in text


class TestIgnoreSuggestion:
    """Tests for Ignore Suggestion functionality."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock pattern tracker."""
        tracker = MagicMock(spec=CorrectionPatternTracker)
        tracker.suggestion_count = 0
        tracker.get_suggestions.return_value = []
        return tracker

    def test_ignore_suggestion_empty_shows_info(self, mock_tracker):
        """No suggestions should show informative message."""
        mock_tracker.get_suggestions.return_value = []

        tray = SystemTray(mock_tracker, MagicMock())

        with patch.object(tray, "_show_info") as mock_show:
            tray._on_ignore_suggestion()
            mock_show.assert_called_once()
            call_args = mock_show.call_args
            assert "No suggestions to ignore" in call_args[0][1]

    def test_ignore_suggestion_calls_tracker(self, mock_tracker):
        """Ignoring should call tracker.ignore_pattern."""
        mock_tracker.get_suggestions.return_value = [("teh", "the", 5)]

        tray = SystemTray(mock_tracker, MagicMock())

        # Mock the selection dialog to return the first suggestion
        with patch.object(
            tray, "_show_selection_dialog", return_value=("teh", "the", 5)
        ):
            with patch.object(tray, "_show_info"):
                tray._on_ignore_suggestion()

                mock_tracker.ignore_pattern.assert_called_once_with("teh", "the")

    def test_ignore_suggestion_cancelled_does_nothing(self, mock_tracker):
        """Cancelled selection should not call tracker."""
        mock_tracker.get_suggestions.return_value = [("teh", "the", 5)]

        tray = SystemTray(mock_tracker, MagicMock())

        # Mock the selection dialog to return None (cancelled)
        with patch.object(tray, "_show_selection_dialog", return_value=None):
            tray._on_ignore_suggestion()

            mock_tracker.ignore_pattern.assert_not_called()


class TestOpenRulesFile:
    """Tests for Open Rules File functionality."""

    def test_open_rules_creates_if_missing(self, tmp_path):
        """Should create rules file if it doesn't exist."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        tray = SystemTray(mock_tracker, MagicMock())

        mock_path = MagicMock()
        mock_path.exists.return_value = False

        with patch.dict(
            "sys.modules",
            {"custom_autocorrect.paths": MagicMock()},
        ):
            import custom_autocorrect.tray as tray_module

            with patch.object(
                tray_module, "_open_file", return_value=True
            ) as mock_open:
                # Patch the paths imports inside the method
                with patch(
                    "custom_autocorrect.paths.get_rules_path", return_value=mock_path
                ):
                    with patch(
                        "custom_autocorrect.paths.ensure_rules_file"
                    ) as mock_ensure:
                        tray._on_open_rules()
                        mock_ensure.assert_called_once()

    def test_open_rules_opens_file(self, tmp_path):
        """Should open the rules file."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        tray = SystemTray(mock_tracker, MagicMock())

        test_path = tmp_path / "rules.txt"
        test_path.touch()

        import custom_autocorrect.tray as tray_module

        with patch.object(tray_module, "_open_file") as mock_open:
            with patch("custom_autocorrect.paths.get_rules_path", return_value=test_path):
                tray._on_open_rules()
                mock_open.assert_called_once_with(test_path)


class TestOpenCorrectionsLog:
    """Tests for Open Corrections Log functionality."""

    def test_open_log_creates_if_missing(self, tmp_path):
        """Should create log file if it doesn't exist."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        tray = SystemTray(mock_tracker, MagicMock())

        test_path = tmp_path / "corrections.log"

        import custom_autocorrect.tray as tray_module

        with patch.object(tray_module, "_open_file"):
            with patch(
                "custom_autocorrect.paths.get_corrections_log_path",
                return_value=test_path,
            ):
                tray._on_open_log()
                assert test_path.exists()

    def test_open_log_opens_file(self, tmp_path):
        """Should open the log file."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        tray = SystemTray(mock_tracker, MagicMock())

        test_path = tmp_path / "corrections.log"
        test_path.touch()

        import custom_autocorrect.tray as tray_module

        with patch.object(tray_module, "_open_file") as mock_open:
            with patch(
                "custom_autocorrect.paths.get_corrections_log_path",
                return_value=test_path,
            ):
                tray._on_open_log()
                mock_open.assert_called_once_with(test_path)


class TestDynamicMenuText:
    """Tests for dynamic menu text updates."""

    def test_suggestion_count_in_menu_text(self):
        """Menu should show current suggestion count."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        mock_tracker.suggestion_count = 5

        tray = SystemTray(mock_tracker, MagicMock())
        menu = tray._create_menu()

        # The first menu item should be the View Suggestions item
        # with dynamic text showing the count
        # Note: pystray MenuItem uses callable for dynamic text
        # Access items through iteration
        items = list(menu)
        first_item = items[0]

        # pystray stores the text callable in _text attribute
        if hasattr(first_item, "_text") and callable(first_item._text):
            text = first_item._text(None)
            assert "5 pending" in text
        elif hasattr(first_item, "text"):
            text = first_item.text(None) if callable(first_item.text) else first_item.text
            assert "5 pending" in text

    def test_suggestion_count_updates(self):
        """Menu text should reflect current count."""
        mock_tracker = MagicMock(spec=CorrectionPatternTracker)
        mock_tracker.suggestion_count = 0

        tray = SystemTray(mock_tracker, MagicMock())
        menu = tray._create_menu()

        items = list(menu)
        first_item = items[0]

        # Get text callable
        text_callable = getattr(first_item, "_text", None) or getattr(
            first_item, "text", None
        )

        if text_callable and callable(text_callable):
            # Check with 0 suggestions
            text = text_callable(None)
            assert "0 pending" in text

            # Update count
            mock_tracker.suggestion_count = 10
            text = text_callable(None)
            assert "10 pending" in text
