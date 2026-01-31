# Phase 1: Development Environment Setup - Execution Plan

## Overview

**Goal**: Get the Windows development environment ready with remote access, Python, git, and GitHub.

**Deliverable**: Working development environment where you can write Python code on Windows (accessed from Mac), run it, and push to GitHub.

**Prerequisites**:
- Windows PC with admin access
- Mac for remote access
- GitHub account

---

## Task Breakdown

### Task 1.1: Set Up Remote Access from Mac to Windows

**Purpose**: Enable development on Windows while working from Mac.

**Option A: Windows Remote Desktop (Recommended for GUI work)**
1. On Windows:
   - Open Settings → System → Remote Desktop
   - Toggle "Enable Remote Desktop" to ON
   - Note the PC name shown (e.g., `DESKTOP-XXXX`)
   - Ensure Windows Firewall allows Remote Desktop connections
2. On Mac:
   - Download "Microsoft Remote Desktop" from Mac App Store
   - Add new PC connection using the Windows PC name or IP address
   - Connect and verify you can see the Windows desktop

**Option B: SSH + VS Code Remote (Recommended for code editing)**
1. On Windows (run PowerShell as Administrator):
   ```powershell
   # Install OpenSSH Server
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

   # Start the service
   Start-Service sshd

   # Set to auto-start on boot
   Set-Service -Name sshd -StartupType 'Automatic'

   # Confirm firewall rule exists
   Get-NetFirewallRule -Name *ssh*
   ```
2. On Mac:
   - Install VS Code if not present
   - Install "Remote - SSH" extension
   - Connect to Windows: `ssh username@windows-ip-address`
   - Open the project folder remotely

**Verification**:
- [ ] Can access Windows desktop or terminal from Mac
- [ ] Can create and edit a test file on Windows from Mac

---

### Task 1.2: Install Python 3.11+ on Windows

**Steps**:
1. Download Python 3.11+ from https://www.python.org/downloads/windows/
2. Run installer with these options:
   - [x] Add Python to PATH (CRITICAL - check this box)
   - [x] Install for all users (recommended)
3. Verify installation in PowerShell:
   ```powershell
   python --version
   # Should show Python 3.11.x or higher

   pip --version
   # Should show pip with Python 3.11
   ```

**Verification**:
- [ ] `python --version` shows 3.11+
- [ ] `pip --version` works
- [ ] Can run `python -c "print('Hello World')"`

---

### Task 1.3: Install Git and Configure Identity

**Steps**:
1. Download Git from https://git-scm.com/download/win
2. Run installer with defaults (or customize if preferred)
3. Configure identity in PowerShell:
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"

   # Verify
   git config --list
   ```
4. (Optional) Set up SSH key for GitHub:
   ```powershell
   ssh-keygen -t ed25519 -C "your.email@example.com"
   # Press Enter to accept default location
   # Optionally add a passphrase

   # Display public key to add to GitHub
   cat ~/.ssh/id_ed25519.pub
   ```
5. Add SSH key to GitHub: Settings → SSH and GPG keys → New SSH key

**Verification**:
- [ ] `git --version` works
- [ ] `git config user.name` shows your name
- [ ] `git config user.email` shows your email
- [ ] (If using SSH) `ssh -T git@github.com` returns success message

---

### Task 1.4: Create GitHub Repository

**Steps**:
1. Go to https://github.com/new
2. Create repository:
   - Name: `custom-autocorrect` (or preferred name)
   - Description: "Windows background app for silent typo correction"
   - Visibility: Private (recommended) or Public
   - [x] Add README
   - [x] Add .gitignore → Python template
   - [ ] License: MIT (optional)
3. Note the repository URL for cloning

**Verification**:
- [ ] Repository visible at github.com/yourusername/custom-autocorrect
- [ ] README.md and .gitignore present

---

### Task 1.5: Clone Repository to Windows

**Steps**:
1. Open PowerShell on Windows
2. Navigate to development directory:
   ```powershell
   cd ~\Documents
   # Or your preferred development location
   ```
3. Clone the repository:
   ```powershell
   # If using SSH:
   git clone git@github.com:yourusername/custom-autocorrect.git

   # If using HTTPS:
   git clone https://github.com/yourusername/custom-autocorrect.git
   ```
4. Enter the project directory:
   ```powershell
   cd custom-autocorrect
   ```

**Verification**:
- [ ] Project folder exists with README.md and .gitignore
- [ ] `git status` shows clean working directory
- [ ] `git remote -v` shows GitHub URL

---

### Task 1.6: Create Virtual Environment and Install Dependencies

**Steps**:
1. Create virtual environment:
   ```powershell
   python -m venv venv
   ```
2. Activate virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1

   # If you get an execution policy error:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   # Then try activating again
   ```
3. Upgrade pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
4. Create `requirements.txt` with initial dependencies:
   ```
   # Core functionality
   keyboard>=0.13.5
   pynput>=1.7.6
   pystray>=0.19.4
   Pillow>=10.0.0

   # Windows-specific
   pywin32>=306

   # Testing
   pytest>=7.4.0
   hypothesis>=6.82.0

   # Packaging
   pyinstaller>=5.13.0
   ```
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

**Verification**:
- [ ] `(venv)` appears in prompt when activated
- [ ] `pip list` shows installed packages
- [ ] `python -c "import keyboard; print('OK')"` works
- [ ] `python -c "import pystray; print('OK')"` works

---

### Task 1.7: Create Basic Project Structure

**Directory Structure**:
```
custom-autocorrect/
├── src/
│   └── custom_autocorrect/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── keystroke_engine.py  # Phase 2
│       ├── rules.py             # Phase 3
│       ├── correction.py        # Phase 4
│       ├── logging.py           # Phase 5
│       ├── password_detect.py   # Phase 6
│       ├── suggestions.py       # Phase 7
│       └── tray.py              # Phase 8
├── tests/
│   ├── __init__.py
│   ├── test_rules.py
│   ├── test_correction.py
│   └── test_suggestions.py
├── resources/
│   └── icon.png                 # Placeholder for tray icon
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py                     # Optional, for editable install
└── pyproject.toml               # Modern Python packaging
```

**Files to Create**:

1. **src/custom_autocorrect/__init__.py**:
   ```python
   """Custom Autocorrect - Silent typo correction for Windows."""
   __version__ = "0.1.0"
   ```

2. **src/custom_autocorrect/main.py**:
   ```python
   """Main entry point for Custom Autocorrect."""

   def main():
       """Start the Custom Autocorrect application."""
       print("Custom Autocorrect starting...")
       print("Press Ctrl+C to exit.")

       try:
           # Placeholder - will be replaced with actual logic
           import time
           while True:
               time.sleep(1)
       except KeyboardInterrupt:
           print("\nExiting...")

   if __name__ == "__main__":
       main()
   ```

3. **tests/__init__.py**: Empty file

4. **tests/test_placeholder.py**:
   ```python
   """Placeholder test to verify pytest works."""

   def test_placeholder():
       """Verify test framework is working."""
       assert True

   def test_imports():
       """Verify core packages can be imported."""
       import keyboard
       import pystray
       assert True
   ```

5. **pyproject.toml**:
   ```toml
   [build-system]
   requires = ["setuptools>=61.0"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "custom-autocorrect"
   version = "0.1.0"
   description = "Silent typo correction for Windows"
   readme = "README.md"
   requires-python = ">=3.11"

   [tool.pytest.ini_options]
   testpaths = ["tests"]
   python_files = "test_*.py"
   ```

6. **resources/icon.png**: Create a simple 64x64 placeholder icon (can be any small PNG)

**Verification**:
- [ ] All directories and files created
- [ ] `python src/custom_autocorrect/main.py` runs and prints startup message
- [ ] `pytest` runs and shows 2 passing tests

---

### Task 1.8: Verify Round-Trip (Edit → Commit → Push → GitHub)

**Steps**:
1. Make a small edit to README.md:
   ```markdown
   # Custom Autocorrect

   Silent typo correction for Windows.

   ## Development Setup

   1. Clone this repository
   2. Create virtual environment: `python -m venv venv`
   3. Activate: `.\venv\Scripts\Activate.ps1`
   4. Install dependencies: `pip install -r requirements.txt`
   5. Run tests: `pytest`
   ```

2. Stage and commit:
   ```powershell
   git add .
   git status  # Review what will be committed
   git commit -m "Initial project structure with placeholder files"
   ```

3. Push to GitHub:
   ```powershell
   git push origin main
   ```

4. Verify on GitHub:
   - Refresh repository page
   - Confirm all files are visible
   - README renders correctly

**Verification**:
- [ ] Commit appears in git log
- [ ] Push succeeds without errors
- [ ] Files visible on GitHub website
- [ ] README displays correctly on GitHub

---

## Files Created/Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `requirements.txt` | Create | Python dependencies |
| `pyproject.toml` | Create | Modern Python project config |
| `src/custom_autocorrect/__init__.py` | Create | Package initialization |
| `src/custom_autocorrect/main.py` | Create | Entry point placeholder |
| `tests/__init__.py` | Create | Test package marker |
| `tests/test_placeholder.py` | Create | Verify pytest works |
| `resources/icon.png` | Create | Tray icon placeholder |
| `README.md` | Modify | Add development setup instructions |
| `.gitignore` | Modify | Ensure venv/ and __pycache__/ excluded |

---

## Acceptance Criteria Satisfied

From **REQ-8: Startup and Lifecycle**:
- [Partial] Criteria 1: PyInstaller is installed (packaging tested in Phase 10)

From **REQ-9: File Storage**:
- [Setup] Development environment ready for implementing file storage features

This phase is infrastructure setup and does not directly satisfy user-facing requirements. It enables all subsequent phases.

---

## Verification Checklist

### Remote Access
- [ ] Can connect to Windows from Mac
- [ ] Can edit files on Windows from Mac

### Python Environment
- [ ] Python 3.11+ installed and in PATH
- [ ] Virtual environment created and activates
- [ ] All dependencies installed successfully

### Git & GitHub
- [ ] Git installed with identity configured
- [ ] Repository created on GitHub
- [ ] Repository cloned to Windows
- [ ] Can push commits to GitHub

### Project Structure
- [ ] All directories created
- [ ] All placeholder files in place
- [ ] `python src/custom_autocorrect/main.py` runs
- [ ] `pytest` passes (2 tests)

### Round-Trip Verified
- [ ] Edit → commit → push → visible on GitHub

---

## Troubleshooting

### Common Issues

**"python is not recognized"**
- Python not added to PATH during installation
- Fix: Reinstall Python with "Add to PATH" checked, or manually add to PATH

**PowerShell execution policy error**
- Windows blocks running scripts by default
- Fix: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**SSH connection refused**
- OpenSSH Server not running
- Fix: `Start-Service sshd` and check firewall

**Git push rejected**
- Authentication issue
- Fix: Set up SSH key or use HTTPS with personal access token

**Import error for keyboard/pystray**
- Package not installed in active venv
- Fix: Ensure venv is activated, reinstall with `pip install -r requirements.txt`

---

## Next Phase

After completing Phase 1, proceed to **Phase 2: Core Keystroke Engine** which will:
- Implement global keyboard hook
- Build word buffer logic
- Detect word boundaries (space delimiter)
- Handle backspace and special keys

Phase 2 depends on having a working Python environment with the `keyboard` library installed.
