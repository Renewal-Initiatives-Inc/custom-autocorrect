"""Global hotkey for adding correction rules.

Phase 9 Implementation:
- Win+Shift+A hotkey registration
- Add Rule dialog with validation
- Rule file appending with UTF-8 support
"""

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Try to import keyboard library
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


def append_rule_to_file(typo: str, correction: str, rules_path: Optional[Path] = None) -> bool:
    """Append a new rule to rules.txt.

    Args:
        typo: The misspelled word.
        correction: The correct replacement.
        rules_path: Optional path to rules file. If None, uses default.

    Returns:
        True if successful, False otherwise.
    """
    if rules_path is None:
        from .paths import get_rules_path

        rules_path = get_rules_path()

    try:
        # Read existing content to check if we need a leading newline
        existing_content = ""
        if rules_path.exists():
            existing_content = rules_path.read_text(encoding="utf-8")

        # Determine if we need a leading newline
        needs_newline = existing_content and not existing_content.endswith("\n")

        # Build the new rule line
        new_rule = f"{typo}={correction}\n"
        if needs_newline:
            new_rule = "\n" + new_rule

        # Append to file
        with rules_path.open("a", encoding="utf-8") as f:
            f.write(new_rule)

        logger.info(f"Added rule to {rules_path}: {typo}={correction}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied writing to {rules_path}: {e}")
        return False
    except OSError as e:
        logger.error(f"Failed to write rule to {rules_path}: {e}")
        return False


def validate_rule_input(typo: str, correction: str) -> Optional[str]:
    """Validate typo and correction input.

    Args:
        typo: The typo to validate.
        correction: The correction to validate.

    Returns:
        Error message if invalid, None if valid.
    """
    typo = typo.strip()
    correction = correction.strip()

    if not typo:
        return "Typo cannot be empty."

    if not correction:
        return "Correction cannot be empty."

    if typo.lower() == correction.lower():
        return "Typo and correction cannot be the same."

    return None


def show_add_rule_dialog() -> Optional[tuple[str, str]]:
    """Show dialog to enter typo and correction.

    Returns:
        Tuple of (typo, correction) if confirmed, None if cancelled.
    """
    result: list[Optional[tuple[str, str]]] = [None]
    done_event = threading.Event()

    def show() -> None:
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.title("Add Correction Rule")
            root.geometry("350x180")
            root.resizable(False, False)

            # Center the window on screen
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"+{x}+{y}")

            # Keep on top
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()

            # Form layout
            frame = tk.Frame(root, padx=20, pady=15)
            frame.pack(fill=tk.BOTH, expand=True)

            # Typo field
            tk.Label(frame, text="Typo (what you type wrong):", anchor="w").pack(
                fill=tk.X
            )
            typo_entry = tk.Entry(frame, font=("Consolas", 11))
            typo_entry.pack(fill=tk.X, pady=(2, 10))
            typo_entry.focus_set()

            # Correction field
            tk.Label(frame, text="Correction (what it should be):", anchor="w").pack(
                fill=tk.X
            )
            correction_entry = tk.Entry(frame, font=("Consolas", 11))
            correction_entry.pack(fill=tk.X, pady=(2, 15))

            def on_submit(event=None) -> None:
                typo = typo_entry.get().strip()
                correction = correction_entry.get().strip()

                error = validate_rule_input(typo, correction)
                if error:
                    messagebox.showerror("Invalid Input", error, parent=root)
                    return

                result[0] = (typo, correction)
                root.destroy()
                done_event.set()

            def on_cancel(event=None) -> None:
                root.destroy()
                done_event.set()

            # Buttons
            btn_frame = tk.Frame(frame)
            btn_frame.pack(fill=tk.X)

            add_btn = tk.Button(
                btn_frame, text="Add Rule", command=on_submit, width=12
            )
            add_btn.pack(side=tk.LEFT, padx=(0, 10))

            cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12)
            cancel_btn.pack(side=tk.LEFT)

            # Keyboard bindings
            root.bind("<Return>", on_submit)
            root.bind("<Escape>", on_cancel)
            correction_entry.bind("<Return>", on_submit)

            # Handle window close
            root.protocol("WM_DELETE_WINDOW", on_cancel)

            root.mainloop()

        except Exception as e:
            logger.error(f"Failed to show add rule dialog: {e}")
            done_event.set()

    # Run dialog in current thread if called from main thread,
    # otherwise in a new thread
    thread = threading.Thread(target=show, daemon=True)
    thread.start()

    # Wait for dialog to complete (with timeout)
    done_event.wait(timeout=300)  # 5 minute timeout

    return result[0]


def show_confirmation(typo: str, correction: str) -> None:
    """Show brief confirmation that rule was added.

    Args:
        typo: The typo that was added.
        correction: The correction that was added.
    """

    def show() -> None:
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            messagebox.showinfo(
                "Rule Added",
                f"New rule added:\n\n{typo} \u2192 {correction}\n\nThe rule is now active.",
                parent=root,
            )
            root.destroy()
        except Exception as e:
            logger.warning(f"Failed to show confirmation: {e}")

    threading.Thread(target=show, daemon=True).start()


class AddRuleHotkey:
    """Manages Win+Shift+A hotkey for adding rules.

    The hotkey opens a dialog to enter a typo and correction,
    validates the input, appends the rule to rules.txt, and
    shows a confirmation.
    """

    HOTKEY = "win+shift+a"

    def __init__(
        self,
        on_rule_added: Optional[Callable[[str, str], None]] = None,
    ):
        """Initialize hotkey handler.

        Args:
            on_rule_added: Optional callback invoked with (typo, correction)
                          after a rule is successfully added.
        """
        if not KEYBOARD_AVAILABLE:
            raise ImportError(
                "The 'keyboard' library is required for hotkey support. "
                "Install it with: pip install keyboard"
            )

        self._on_rule_added = on_rule_added
        self._registered = False
        self._hotkey_id = None

    @property
    def is_registered(self) -> bool:
        """Check if the hotkey is currently registered."""
        return self._registered

    def register(self) -> None:
        """Register the global hotkey.

        The hotkey will open the add-rule dialog when pressed.
        """
        if self._registered:
            logger.warning("Hotkey already registered")
            return

        try:
            self._hotkey_id = keyboard.add_hotkey(
                self.HOTKEY,
                self._on_hotkey_pressed,
                suppress=False,
            )
            self._registered = True
            logger.info(f"Registered hotkey: {self.HOTKEY}")
        except Exception as e:
            logger.error(f"Failed to register hotkey {self.HOTKEY}: {e}")
            raise

    def unregister(self) -> None:
        """Unregister the hotkey."""
        if not self._registered:
            return

        try:
            if self._hotkey_id is not None:
                keyboard.remove_hotkey(self._hotkey_id)
                self._hotkey_id = None
            self._registered = False
            logger.info(f"Unregistered hotkey: {self.HOTKEY}")
        except Exception as e:
            logger.warning(f"Error unregistering hotkey: {e}")
            self._registered = False

    def _on_hotkey_pressed(self) -> None:
        """Handle hotkey press event.

        Opens the dialog in a separate thread to avoid blocking.
        """
        logger.debug("Hotkey pressed, opening add-rule dialog")

        def handle_dialog():
            result = show_add_rule_dialog()

            if result is None:
                logger.debug("Add rule dialog cancelled")
                return

            typo, correction = result

            # Append to file
            if append_rule_to_file(typo, correction):
                # Show confirmation
                show_confirmation(typo, correction)

                # Invoke callback if provided
                if self._on_rule_added:
                    try:
                        self._on_rule_added(typo, correction)
                    except Exception as e:
                        logger.error(f"Error in on_rule_added callback: {e}")
            else:
                # Show error
                self._show_error(
                    "Failed to add rule. Check that rules.txt is writable."
                )

        # Run in thread to avoid blocking keyboard processing
        threading.Thread(target=handle_dialog, daemon=True).start()

    def _show_error(self, message: str) -> None:
        """Show error dialog."""

        def show():
            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                messagebox.showerror("Error", message, parent=root)
                root.destroy()
            except Exception as e:
                logger.warning(f"Failed to show error dialog: {e}")

        threading.Thread(target=show, daemon=True).start()
