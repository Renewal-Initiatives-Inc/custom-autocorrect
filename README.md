# Custom Autocorrect

Silent typo correction for Windows.

A lightweight Windows background application that silently corrects known typos based on user-defined rules. The app monitors keystrokes system-wide, performs corrections via backspace+retype, and passively tracks potential typos for user review.

## Features

- **Silent Correction**: Automatically fixes your known typos as you type
- **User-Defined Rules**: Only corrects patterns you've explicitly added
- **Casing Preservation**: Maintains lowercase, Capitalized, or UPPERCASE
- **Pattern Suggestions**: Tracks frequently-typed non-dictionary words for review
- **System Tray Integration**: Unobtrusive background operation
- **Ctrl+Z Friendly**: Corrections can be undone with standard undo

## Requirements

- Windows 10/11
- Python 3.11+
- Administrator privileges (for keyboard hooks)

## Development Setup

### On Windows

1. **Install Python 3.11+**
   - Download from https://www.python.org/downloads/windows/
   - **Important**: Check "Add Python to PATH" during installation

2. **Clone the repository**
   ```powershell
   git clone https://github.com/yourusername/custom-autocorrect.git
   cd custom-autocorrect
   ```

3. **Create and activate virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Generate the tray icon**
   ```powershell
   python resources/create_icon.py
   ```

6. **Run tests**
   ```powershell
   pytest
   ```

7. **Run the application** (placeholder for now)
   ```powershell
   python src/custom_autocorrect/main.py
   ```

### Remote Development from Mac

See [technology_decisions.md](technology_decisions.md) for remote access setup options:
- Windows Remote Desktop
- SSH + VS Code Remote

## Project Structure

```
custom-autocorrect/
├── src/custom_autocorrect/     # Source code
│   ├── main.py                 # Entry point
│   ├── keystroke_engine.py     # Keyboard monitoring
│   ├── rules.py                # Rule loading/matching
│   ├── correction.py           # Text replacement
│   ├── logging.py              # Correction logging
│   ├── password_detect.py      # Password field detection
│   ├── suggestions.py          # Pattern tracking
│   └── tray.py                 # System tray
├── tests/                      # Test suite
├── resources/                  # Icons and assets
├── requirements.txt            # Python dependencies
└── pyproject.toml             # Project configuration
```

## User Files

When running, the app creates files in `Documents/CustomAutocorrect/`:

| File | Purpose |
|------|---------|
| `rules.txt` | Your correction rules (`typo=correction`) |
| `suggestions.txt` | Detected potential typos |
| `ignore.txt` | Words to never suggest |
| `corrections.log` | Rolling log of corrections made |
| `custom-words.txt` | Words to treat as valid |

## Usage

*(Coming in later phases)*

- **Add a rule**: Press `Win+Shift+A` or edit `rules.txt`
- **View suggestions**: Right-click tray icon → View Suggestions
- **Check corrections**: Right-click tray icon → Open Corrections Log

## Status

**Phase 1: Development Environment Setup** - In Progress

See [implementation_plan.md](implementation_plan.md) for the full roadmap.

## License

MIT
