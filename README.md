# Custom Autocorrect

Silent typo correction for Windows.

A lightweight Windows background application that silently corrects known typos based on user-defined rules. The app monitors keystrokes system-wide, performs corrections via backspace+retype, and passively tracks potential typos for user review.

## Features

- **Silent Correction**: Automatically fixes your known typos as you type
- **User-Defined Rules**: Only corrects patterns you've explicitly added
- **Casing Preservation**: Maintains lowercase, Capitalized, or UPPERCASE
- **Pattern Suggestions**: Detects words you frequently correct via backspace
- **System Tray Integration**: Unobtrusive background operation with menu access
- **Quick Rule Addition**: Press Win+Shift+A anywhere to add a new rule
- **Ctrl+Z Friendly**: Corrections can be undone with standard undo

## Installation

### Download (Recommended)

1. Go to the [Releases page](https://github.com/yourusername/custom-autocorrect/releases)
2. Download `CustomAutocorrect.exe` from the latest release
3. Run the executable (right-click → Run as Administrator for best results)
4. A pillow icon appears in your system tray - you're ready!

**Optional: Auto-start with Windows**
- Press `Win+R`, type `shell:startup`, press Enter
- Copy `CustomAutocorrect.exe` to the opened folder

### Requirements

- Windows 10 or Windows 11
- Administrator privileges recommended (for global keyboard access)

## Usage

### Quick Start

1. Run `CustomAutocorrect.exe`
2. Look for the pillow icon in your system tray
3. Add your first rule: Press **Win+Shift+A**
4. Enter a typo (e.g., "teh") and its correction (e.g., "the")
5. Start typing! Typos matching your rules are corrected automatically

### Adding Rules

**Via Hotkey (Recommended):**
- Press **Win+Shift+A** anywhere
- Enter the typo and correction
- The rule is immediately active

**Via File:**
- Right-click the tray icon → Open Rules File
- Add rules in format: `typo=correction`
- Save the file; rules reload automatically

### Example Rules

```
# Common typos
teh=the
adn=and
hte=the
taht=that
waht=what

# Your personal patterns
recieve=receive
occured=occurred
```

### System Tray Menu

Right-click the tray icon for:
- **View Suggestions**: See patterns detected from your typing
- **Ignore Suggestion**: Stop suggesting a specific pattern
- **Open Rules File**: Edit your correction rules
- **Open Corrections Log**: See recent corrections made
- **Exit**: Close the application

### Pattern Detection

The app learns from your typing behavior:
- When you type a word, backspace to erase it, and type something different
- After 5 occurrences, it appears in your suggestions
- Review suggestions in the tray menu
- Copy useful patterns to your rules file

## User Files

The app stores data in `Documents\CustomAutocorrect\`:

| File | Purpose |
|------|---------|
| `rules.txt` | Your correction rules (`typo=correction`) |
| `suggestions.txt` | Detected correction patterns |
| `ignore.txt` | Patterns to never suggest |
| `corrections.log` | Rolling log of recent corrections |
| `custom-words.txt` | Words to treat as valid (not typos) |

## Antivirus Notes

Some antivirus software may flag `CustomAutocorrect.exe` as suspicious. This is a common [false positive with PyInstaller](https://github.com/pyinstaller/pyinstaller/issues/5854) applications.

**To add an exception in Windows Defender:**
1. Open Windows Security
2. Go to Virus & threat protection → Manage settings
3. Scroll to Exclusions → Add or remove exclusions
4. Add the `CustomAutocorrect.exe` file

The application is open source - you can review the code or build from source.

## Building from Source

### Requirements

- Windows 10/11
- Python 3.11+
- Git

### Setup

```powershell
# Clone the repository
git clone https://github.com/yourusername/custom-autocorrect.git
cd custom-autocorrect

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Generate icons
python resources/create_icon.py

# Run tests
pytest

# Run from source
python -m custom_autocorrect
```

### Building the Executable

```powershell
# Full build (runs tests first)
python build.py

# Quick build (skip tests)
python build.py --no-test
```

The executable will be at `dist\CustomAutocorrect.exe`.

## Project Structure

```
custom-autocorrect/
├── src/custom_autocorrect/     # Source code
│   ├── main.py                 # Entry point
│   ├── keystroke_engine.py     # Keyboard monitoring
│   ├── rules.py                # Rule loading/matching
│   ├── correction.py           # Text replacement
│   ├── correction_log.py       # Correction logging
│   ├── password_detect.py      # Password field detection
│   ├── suggestions.py          # Pattern tracking
│   ├── tray.py                 # System tray
│   ├── hotkey.py               # Win+Shift+A handler
│   └── paths.py                # File path management
├── tests/                      # Test suite
├── resources/                  # Icons and dictionary
├── CustomAutocorrect.spec      # PyInstaller configuration
├── build.py                    # Build script
└── pyproject.toml              # Project configuration
```

## Version History

- **v1.0.0** - First release
  - Silent typo correction with user-defined rules
  - Casing preservation (lowercase, Capitalized, UPPERCASE)
  - Pattern suggestion from typing behavior
  - System tray with menu access
  - Win+Shift+A hotkey for quick rule addition
  - Password field protection

## License

MIT
