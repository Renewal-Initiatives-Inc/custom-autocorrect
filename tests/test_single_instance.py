"""Tests for single instance enforcement."""

import pytest
from unittest.mock import MagicMock, patch
import sys


class TestSingleInstanceLock:
    """Tests for SingleInstanceLock class."""

    def test_acquire_returns_true_first_time(self):
        """First instance should acquire lock successfully."""
        # Mock win32event to simulate successful mutex creation
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345  # Fake handle

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 0  # No error

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': MagicMock(ERROR_ALREADY_EXISTS=183),
        }):
            from custom_autocorrect.single_instance import SingleInstanceLock

            lock = SingleInstanceLock("TestMutex")
            result = lock.acquire()

            assert result is True
            assert lock.is_acquired is True

    def test_acquire_returns_false_when_already_running(self):
        """Second instance should fail to acquire lock."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 183  # ERROR_ALREADY_EXISTS

        mock_winerror = MagicMock()
        mock_winerror.ERROR_ALREADY_EXISTS = 183

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': mock_winerror,
        }):
            from custom_autocorrect.single_instance import SingleInstanceLock

            lock = SingleInstanceLock("TestMutex")
            result = lock.acquire()

            assert result is False
            assert lock.is_acquired is False
            # Should have closed the handle
            mock_win32api.CloseHandle.assert_called_once()

    def test_acquire_idempotent(self):
        """Calling acquire multiple times returns same result."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 0

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': MagicMock(ERROR_ALREADY_EXISTS=183),
        }):
            from custom_autocorrect.single_instance import SingleInstanceLock

            lock = SingleInstanceLock("TestMutex")
            lock.acquire()
            result = lock.acquire()  # Second call

            assert result is True
            # CreateMutex should only be called once
            assert mock_win32event.CreateMutex.call_count == 1

    def test_release_cleans_up(self):
        """Release should close the mutex handle."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 0

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': MagicMock(ERROR_ALREADY_EXISTS=183),
        }):
            from custom_autocorrect.single_instance import SingleInstanceLock

            lock = SingleInstanceLock("TestMutex")
            lock.acquire()
            lock.release()

            mock_win32api.CloseHandle.assert_called_once_with(12345)
            assert lock.is_acquired is False

    def test_context_manager(self):
        """Lock should work as context manager."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 0

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': MagicMock(ERROR_ALREADY_EXISTS=183),
        }):
            from custom_autocorrect.single_instance import SingleInstanceLock

            lock = SingleInstanceLock("TestMutex")

            with lock:
                assert lock.is_acquired is True

            assert lock.is_acquired is False

    def test_graceful_fallback_without_win32(self):
        """Should allow running if win32event not available."""
        # Remove win32event from modules to simulate ImportError
        with patch.dict(sys.modules, {'win32event': None}):
            # Force reimport to trigger ImportError handling
            import importlib
            from custom_autocorrect import single_instance
            importlib.reload(single_instance)

            lock = single_instance.SingleInstanceLock("TestMutex")
            result = lock.acquire()

            # Should succeed (fail open)
            assert result is True


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_is_another_instance_running_false_when_not_running(self):
        """Should return False when no other instance."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 0

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': MagicMock(ERROR_ALREADY_EXISTS=183),
        }):
            from custom_autocorrect.single_instance import is_another_instance_running

            result = is_another_instance_running()
            assert result is False

    def test_is_another_instance_running_true_when_running(self):
        """Should return True when another instance is running."""
        mock_win32event = MagicMock()
        mock_win32event.CreateMutex.return_value = 12345

        mock_win32api = MagicMock()
        mock_win32api.GetLastError.return_value = 183  # ERROR_ALREADY_EXISTS

        mock_winerror = MagicMock()
        mock_winerror.ERROR_ALREADY_EXISTS = 183

        with patch.dict(sys.modules, {
            'win32event': mock_win32event,
            'win32api': mock_win32api,
            'winerror': mock_winerror,
        }):
            from custom_autocorrect.single_instance import is_another_instance_running

            result = is_another_instance_running()
            assert result is True
