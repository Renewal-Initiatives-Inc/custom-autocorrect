"""System tray integration using pystray.

Phase 8 Implementation:
- Tray icon display with "Custom Autocorrect" tooltip
- Right-click menu:
  - View Suggestions (N pending) - shows current suggestions
  - Ignore Suggestion... - select and ignore patterns
  - Separator
  - Open Rules File - opens rules.txt in default editor
  - Open Corrections Log - opens corrections.log in default editor
  - Separator
  - Exit - clean shutdown
"""

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import Icon, Menu, MenuItem

    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

if TYPE_CHECKING:
    from .suggestions import CorrectionPatternTracker

logger = logging.getLogger(__name__)


def _get_bundled_icon_path() -> Optional[Path]:
    """Get path to bundled icon.png resource.

    Returns:
        Path to icon.png if found, None otherwise.
    """
    # Use the centralized path helper that handles PyInstaller bundles
    from .paths import get_icon_path
    return get_icon_path()


def _create_icon_image(size: int = 64) -> Image.Image:
    """Create a pillow-shaped tray icon programmatically.

    Args:
        size: Icon size in pixels.

    Returns:
        PIL Image object.
    """
    import math

    # Create a new image with a soft blue background
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))  # Nice blue
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    margin = size // 8
    pillow_width = size - 2 * margin

    # Pillow body coordinates
    pillow_left = margin
    pillow_right = size - margin
    pillow_top = margin + size // 8
    pillow_bottom = size - margin - size // 12
    corner_radius = size // 6

    # Draw the main pillow body (cream white colored)
    pillow_color = (255, 250, 240, 255)

    # Draw rounded rectangle for pillow
    draw.rounded_rectangle(
        [(pillow_left, pillow_top), (pillow_right, pillow_bottom)],
        radius=corner_radius,
        fill=pillow_color,
        outline=(200, 195, 185, 255),
        width=1,
    )

    # Add pillow "puffiness" - a curved line in the middle
    mid_y = (pillow_top + pillow_bottom) // 2
    curve_points = []
    for i in range(pillow_left + corner_radius, pillow_right - corner_radius + 1, 2):
        offset = int(math.sin((i - pillow_left) / pillow_width * math.pi) * 3)
        curve_points.append((i, mid_y + offset))

    if len(curve_points) >= 2:
        draw.line(curve_points, fill=(220, 215, 205, 255), width=1)

    # Add corner tufts
    tuft_color = (230, 225, 215, 255)
    tuft_size = size // 16

    draw.arc(
        [
            (pillow_left - tuft_size // 2, pillow_top - tuft_size // 2),
            (pillow_left + tuft_size, pillow_top + tuft_size),
        ],
        start=0,
        end=90,
        fill=tuft_color,
        width=2,
    )

    draw.arc(
        [
            (pillow_right - tuft_size, pillow_top - tuft_size // 2),
            (pillow_right + tuft_size // 2, pillow_top + tuft_size),
        ],
        start=90,
        end=180,
        fill=tuft_color,
        width=2,
    )

    # Add small "z"s for sleep motif
    z_x = size - margin - size // 6
    z_y = margin + size // 16
    z_color = (255, 255, 255, 200)
    draw.text((z_x, z_y), "z", fill=z_color)
    draw.text((z_x + size // 20, z_y - size // 20), "z", fill=z_color)

    return img


def _open_file(path: Path) -> bool:
    """Open a file with the default system application.

    Args:
        path: Path to the file to open.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
        return True
    except Exception as e:
        logger.error(f"Failed to open file {path}: {e}")
        return False


class SystemTray:
    """System tray icon and menu for Custom Autocorrect.

    Provides a tray icon with right-click menu for:
    - Viewing and managing suggestions
    - Opening configuration files
    - Clean application exit
    """

    def __init__(
        self,
        pattern_tracker: "CorrectionPatternTracker",
        on_exit: Callable[[], None],
    ):
        """Initialize system tray.

        Args:
            pattern_tracker: For accessing suggestions and ignore functionality.
            on_exit: Callback to trigger clean app shutdown.
        """
        if not PYSTRAY_AVAILABLE:
            raise ImportError(
                "pystray is required for system tray support. "
                "Install it with: pip install pystray"
            )

        self._tracker = pattern_tracker
        self._exit_callback = on_exit
        self._icon: Optional[Icon] = None
        self._running = False

    def _load_icon(self) -> Image.Image:
        """Load icon image from bundled resources or create programmatically.

        Returns:
            PIL Image object for the tray icon.
        """
        # Try bundled icon first
        icon_path = _get_bundled_icon_path()
        if icon_path:
            try:
                return Image.open(icon_path)
            except Exception as e:
                logger.warning(f"Failed to load bundled icon: {e}")

        # Fall back to programmatic creation
        logger.debug("Creating icon programmatically")
        return _create_icon_image()

    def _create_menu(self) -> Menu:
        """Create the right-click context menu.

        Returns:
            pystray Menu object.
        """
        return Menu(
            MenuItem(
                lambda item: f"View Suggestions ({self._tracker.suggestion_count} pending)",
                self._on_view_suggestions,
            ),
            MenuItem("Ignore Suggestion...", self._on_ignore_suggestion),
            Menu.SEPARATOR,
            MenuItem("Open Rules File", self._on_open_rules),
            MenuItem("Open Corrections Log", self._on_open_log),
            MenuItem(
                "Restore Rules Backup",
                self._on_restore_backup,
                visible=lambda item: self._backup_exists(),
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Start with Windows",
                self._on_toggle_startup,
                checked=lambda item: self._is_startup_enabled(),
            ),
            Menu.SEPARATOR,
            MenuItem("Exit", self._on_exit),
        )

    def start(self) -> None:
        """Start the system tray icon.

        The icon runs in a detached thread to avoid blocking.
        """
        if self._running:
            return

        image = self._load_icon()
        self._icon = Icon(
            name="CustomAutocorrect",
            icon=image,
            title="Custom Autocorrect",
            menu=self._create_menu(),
        )
        self._running = True

        # Run detached so it doesn't block
        self._icon.run_detached()
        logger.debug("System tray started")

    def stop(self) -> None:
        """Stop and remove the system tray icon."""
        if self._icon and self._running:
            try:
                self._icon.stop()
            except Exception as e:
                logger.debug(f"Error stopping tray icon: {e}")
            finally:
                self._running = False
                logger.debug("System tray stopped")

    def _on_view_suggestions(self) -> None:
        """Handle 'View Suggestions' menu item click."""
        suggestions = self._tracker.get_suggestions()

        if not suggestions:
            self._show_info(
                "Suggestions",
                "No suggestions yet.\n\n"
                "Type words, then erase and retype them differently.\n"
                "After 5 corrections, the pattern will appear here.",
            )
            return

        # Format suggestions for display
        lines = ["Current correction patterns:\n"]
        for typo, correction, count in suggestions:
            lines.append(f"  {typo} → {correction} ({count} times)")
        lines.append("\nTo enable: copy to rules.txt")
        lines.append("To ignore: use 'Ignore Suggestion' menu")

        self._show_text_dialog("Suggestions", "\n".join(lines))

    def _on_ignore_suggestion(self) -> None:
        """Handle 'Ignore Suggestion' menu item click."""
        suggestions = self._tracker.get_suggestions()

        if not suggestions:
            self._show_info("Ignore Suggestion", "No suggestions to ignore.")
            return

        # Show selection dialog
        selected = self._show_selection_dialog(
            "Ignore Suggestion",
            "Select pattern to ignore:",
            suggestions,
        )

        if selected:
            typo, correction, _ = selected
            self._tracker.ignore_pattern(typo, correction)
            self._show_info(
                "Pattern Ignored",
                f"'{typo} → {correction}' will no longer be suggested.",
            )

    def _on_open_rules(self) -> None:
        """Handle 'Open Rules File' menu item click."""
        from .paths import ensure_rules_file, get_rules_path

        path = get_rules_path()
        if not path.exists():
            ensure_rules_file()

        _open_file(path)

    def _on_open_log(self) -> None:
        """Handle 'Open Corrections Log' menu item click."""
        from .paths import get_corrections_log_path

        path = get_corrections_log_path()
        if not path.exists():
            path.touch()

        _open_file(path)

    def _is_startup_enabled(self) -> bool:
        """Check if auto-start with Windows is enabled."""
        try:
            from .startup import is_startup_enabled
            return is_startup_enabled()
        except Exception as e:
            logger.debug(f"Error checking startup status: {e}")
            return False

    def _backup_exists(self) -> bool:
        """Check if a rules backup exists."""
        try:
            from .rules import backup_exists
            return backup_exists()
        except Exception as e:
            logger.debug(f"Error checking backup: {e}")
            return False

    def _on_restore_backup(self) -> None:
        """Handle 'Restore Rules Backup' menu item click."""
        try:
            from .rules import get_backup_info, restore_from_backup

            info = get_backup_info()
            if not info:
                self._show_info("No Backup", "No backup file found.")
                return

            # Confirm restore
            msg = (
                f"Restore rules from backup?\n\n"
                f"Backup created: {info['modified'].strftime('%Y-%m-%d %H:%M')}\n"
                f"Rules in backup: {info['rule_count']}\n\n"
                f"Your current rules.txt will be replaced."
            )

            if self._confirm_action("Restore Backup", msg):
                if restore_from_backup():
                    self._show_info(
                        "Backup Restored",
                        f"Rules restored from backup.\n"
                        f"{info['rule_count']} rules now active."
                    )
                else:
                    self._show_info(
                        "Restore Failed",
                        "Could not restore rules from backup.\n"
                        "Check the log for details."
                    )
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            self._show_info("Error", f"Failed to restore backup: {e}")

    def _on_toggle_startup(self) -> None:
        """Handle 'Start with Windows' menu item click."""
        try:
            from .startup import is_startup_enabled, enable_startup, disable_startup

            if is_startup_enabled():
                if disable_startup():
                    self._show_info(
                        "Startup Disabled",
                        "Custom Autocorrect will no longer start with Windows."
                    )
                else:
                    self._show_info(
                        "Error",
                        "Failed to disable auto-start."
                    )
            else:
                if enable_startup():
                    self._show_info(
                        "Startup Enabled",
                        "Custom Autocorrect will now start automatically with Windows."
                    )
                else:
                    self._show_info(
                        "Error",
                        "Failed to enable auto-start.\n\n"
                        "You can manually add the app to your Startup folder:\n"
                        "1. Press Win+R, type 'shell:startup'\n"
                        "2. Copy CustomAutocorrect.exe to that folder"
                    )
        except Exception as e:
            logger.error(f"Error toggling startup: {e}")
            self._show_info("Error", f"Failed to toggle startup: {e}")

    def _on_exit(self) -> None:
        """Handle 'Exit' menu item click."""
        logger.info("Exit requested from system tray")
        self.stop()
        self._exit_callback()

    def _show_info(self, title: str, message: str) -> None:
        """Show a simple info dialog.

        Args:
            title: Dialog title.
            message: Message to display.
        """

        def show() -> None:
            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()
                # Bring dialog to front
                root.attributes("-topmost", True)
                messagebox.showinfo(title, message, parent=root)
                root.destroy()
            except Exception as e:
                logger.warning(f"Failed to show info dialog: {e}")

        threading.Thread(target=show, daemon=True).start()

    def _confirm_action(self, title: str, message: str) -> bool:
        """Show a confirmation dialog.

        Args:
            title: Dialog title.
            message: Message to display.

        Returns:
            True if user confirmed, False otherwise.
        """
        result = [False]
        done_event = threading.Event()

        def show() -> None:
            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                result[0] = messagebox.askyesno(title, message, parent=root)
                root.destroy()
            except Exception as e:
                logger.warning(f"Failed to show confirm dialog: {e}")
            finally:
                done_event.set()

        thread = threading.Thread(target=show, daemon=True)
        thread.start()
        done_event.wait(timeout=60)  # 1 minute timeout

        return result[0]

    def _show_text_dialog(self, title: str, text: str) -> None:
        """Show a dialog with scrollable text.

        Args:
            title: Dialog title.
            text: Text content to display.
        """

        def show() -> None:
            try:
                import tkinter as tk
                from tkinter import scrolledtext

                root = tk.Tk()
                root.title(title)
                root.geometry("450x350")
                root.attributes("-topmost", True)

                # Create scrolled text widget
                text_widget = scrolledtext.ScrolledText(
                    root, wrap=tk.WORD, font=("Consolas", 10)
                )
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, text)
                text_widget.config(state=tk.DISABLED)

                # Close button
                close_btn = tk.Button(root, text="Close", command=root.destroy)
                close_btn.pack(pady=(0, 10))

                root.mainloop()
            except Exception as e:
                logger.warning(f"Failed to show text dialog: {e}")
                # Fall back to simple info dialog
                self._show_info(title, text)

        threading.Thread(target=show, daemon=True).start()

    def _show_selection_dialog(
        self,
        title: str,
        prompt: str,
        suggestions: list[tuple[str, str, int]],
    ) -> Optional[tuple[str, str, int]]:
        """Show a dialog to select from suggestions.

        Args:
            title: Dialog title.
            prompt: Prompt text.
            suggestions: List of (typo, correction, count) tuples.

        Returns:
            Selected suggestion tuple, or None if cancelled.
        """
        result: list[Optional[tuple[str, str, int]]] = [None]
        done_event = threading.Event()

        def show() -> None:
            try:
                import tkinter as tk
                from tkinter import ttk

                root = tk.Tk()
                root.title(title)
                root.geometry("400x300")
                root.attributes("-topmost", True)

                # Prompt label
                label = tk.Label(root, text=prompt, font=("Segoe UI", 10))
                label.pack(pady=(10, 5))

                # Listbox with scrollbar
                frame = tk.Frame(root)
                frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                scrollbar = tk.Scrollbar(frame)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                listbox = tk.Listbox(
                    frame,
                    yscrollcommand=scrollbar.set,
                    font=("Consolas", 10),
                    selectmode=tk.SINGLE,
                )
                listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.config(command=listbox.yview)

                # Populate listbox
                for typo, correction, count in suggestions:
                    listbox.insert(tk.END, f"{typo} → {correction} ({count} times)")

                # Select first item
                if suggestions:
                    listbox.selection_set(0)

                def on_ignore() -> None:
                    selection = listbox.curselection()
                    if selection:
                        idx = selection[0]
                        result[0] = suggestions[idx]
                    root.destroy()
                    done_event.set()

                def on_cancel() -> None:
                    root.destroy()
                    done_event.set()

                # Buttons
                btn_frame = tk.Frame(root)
                btn_frame.pack(pady=10)

                ignore_btn = tk.Button(
                    btn_frame, text="Ignore Selected", command=on_ignore
                )
                ignore_btn.pack(side=tk.LEFT, padx=5)

                cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
                cancel_btn.pack(side=tk.LEFT, padx=5)

                # Handle window close
                root.protocol("WM_DELETE_WINDOW", on_cancel)

                root.mainloop()
            except Exception as e:
                logger.warning(f"Failed to show selection dialog: {e}")
                done_event.set()

        thread = threading.Thread(target=show, daemon=True)
        thread.start()

        # Wait for dialog to complete (with timeout)
        done_event.wait(timeout=300)  # 5 minute timeout

        return result[0]
