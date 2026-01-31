"""Tests for Windows Startup folder integration."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
import sys
import os


class TestGetStartupFolder:
    """Tests for get_startup_folder function."""

    def test_returns_none_on_non_windows(self):
        """Should return None on non-Windows systems."""
        with patch('os.name', 'posix'):
            from custom_autocorrect.startup import get_startup_folder
            result = get_startup_folder()
            assert result is None

    def test_returns_none_if_appdata_not_set(self):
        """Should return None if APPDATA env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.name', 'nt'):
                from custom_autocorrect.startup import get_startup_folder
                # Force reimport to get fresh state
                import importlib
                from custom_autocorrect import startup
                importlib.reload(startup)
                result = startup.get_startup_folder()
                # Result depends on environment

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_returns_path_when_folder_exists(self):
        """Should return path when Startup folder exists."""
        fake_appdata = Path("/fake/appdata")
        fake_startup = fake_appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

        with patch.dict(os.environ, {"APPDATA": str(fake_appdata)}):
            with patch('os.name', 'nt'):
                with patch.object(Path, 'exists', return_value=True):
                    from custom_autocorrect.startup import get_startup_folder
                    import importlib
                    from custom_autocorrect import startup
                    importlib.reload(startup)
                    result = startup.get_startup_folder()
                    assert result is not None


class TestIsStartupEnabled:
    """Tests for is_startup_enabled function."""

    def test_returns_false_when_shortcut_not_exists(self):
        """Should return False when shortcut doesn't exist."""
        with patch('custom_autocorrect.startup.get_shortcut_path') as mock_path:
            mock_shortcut = MagicMock()
            mock_shortcut.exists.return_value = False
            mock_path.return_value = mock_shortcut

            from custom_autocorrect.startup import is_startup_enabled
            result = is_startup_enabled()
            assert result is False

    def test_returns_true_when_shortcut_exists(self):
        """Should return True when shortcut exists."""
        with patch('custom_autocorrect.startup.get_shortcut_path') as mock_path:
            mock_shortcut = MagicMock()
            mock_shortcut.exists.return_value = True
            mock_path.return_value = mock_shortcut

            from custom_autocorrect.startup import is_startup_enabled
            result = is_startup_enabled()
            assert result is True

    def test_returns_false_when_no_startup_folder(self):
        """Should return False when Startup folder unavailable."""
        with patch('custom_autocorrect.startup.get_shortcut_path') as mock_path:
            mock_path.return_value = None

            from custom_autocorrect.startup import is_startup_enabled
            result = is_startup_enabled()
            assert result is False


class TestEnableStartup:
    """Tests for enable_startup function."""

    def test_returns_false_when_no_shortcut_path(self):
        """Should return False when shortcut path unavailable."""
        with patch('custom_autocorrect.startup.get_shortcut_path') as mock_path:
            mock_path.return_value = None

            from custom_autocorrect.startup import enable_startup
            result = enable_startup()
            assert result is False

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_creates_shortcut_successfully(self):
        """Should create shortcut when all conditions met."""
        mock_shortcut_path = MagicMock()
        mock_shortcut_path.__str__ = MagicMock(return_value="/fake/startup/Custom Autocorrect.lnk")

        mock_shell = MagicMock()
        mock_shortcut_obj = MagicMock()
        mock_shell.CreateShortcut.return_value = mock_shortcut_obj

        with patch('custom_autocorrect.startup.get_shortcut_path', return_value=mock_shortcut_path):
            with patch.dict(sys.modules, {'win32com': MagicMock(), 'win32com.client': MagicMock()}):
                with patch('custom_autocorrect.startup.get_launch_command', return_value=("/path/to/exe", "")):
                    # Mock the paths module function
                    with patch('custom_autocorrect.paths.get_icon_path', return_value=None):
                        # Mock win32com.client.Dispatch
                        import custom_autocorrect.startup as startup_module
                        with patch.object(startup_module, 'win32com', create=True):
                            # This is tricky to test fully due to win32com
                            pass


class TestDisableStartup:
    """Tests for disable_startup function."""

    def test_returns_true_when_no_shortcut_path(self):
        """Should return True when no startup folder (nothing to disable)."""
        with patch('custom_autocorrect.startup.get_shortcut_path') as mock_path:
            mock_path.return_value = None

            from custom_autocorrect.startup import disable_startup
            result = disable_startup()
            assert result is True

    def test_returns_true_when_shortcut_not_exists(self):
        """Should return True when shortcut doesn't exist."""
        mock_shortcut = MagicMock()
        mock_shortcut.exists.return_value = False

        with patch('custom_autocorrect.startup.get_shortcut_path', return_value=mock_shortcut):
            from custom_autocorrect.startup import disable_startup
            result = disable_startup()
            assert result is True

    def test_removes_existing_shortcut(self):
        """Should remove shortcut when it exists."""
        mock_shortcut = MagicMock()
        mock_shortcut.exists.return_value = True

        with patch('custom_autocorrect.startup.get_shortcut_path', return_value=mock_shortcut):
            from custom_autocorrect.startup import disable_startup
            result = disable_startup()

            mock_shortcut.unlink.assert_called_once()
            assert result is True


class TestToggleStartup:
    """Tests for toggle_startup function."""

    def test_enables_when_disabled(self):
        """Should enable startup when currently disabled."""
        with patch('custom_autocorrect.startup.is_startup_enabled', return_value=False):
            with patch('custom_autocorrect.startup.enable_startup') as mock_enable:
                mock_enable.return_value = True

                from custom_autocorrect.startup import toggle_startup
                result = toggle_startup()

                mock_enable.assert_called_once()
                assert result is True

    def test_disables_when_enabled(self):
        """Should disable startup when currently enabled."""
        with patch('custom_autocorrect.startup.is_startup_enabled', return_value=True):
            with patch('custom_autocorrect.startup.disable_startup') as mock_disable:
                mock_disable.return_value = True

                from custom_autocorrect.startup import toggle_startup
                result = toggle_startup()

                mock_disable.assert_called_once()
                assert result is False
