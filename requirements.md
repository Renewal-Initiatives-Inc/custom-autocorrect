# Requirements: Custom Autocorrect

## 1. Introduction

### Project Context
When typing quickly, the user consistently makes the same 10-20 typos. Current spellcheck solutions only highlight errors (red squiggly lines) rather than silently fixing them. The user wants automatic, silent correction of their personal typo patterns—no interruption, no confirmation, just fixed.

### What We're Building
A lightweight Windows application that runs in the background, watches keystrokes, and silently corrects known typos based on user-defined rules. The app also passively tracks potential typos (words not in dictionary typed 5+ times) and suggests new rules without auto-applying them.

### Why We're Building It
- **Double interruption problem**: Noticing a typo AND fixing it breaks writing flow
- **Existing solutions fall short**:
  - Google Docs substitutions only work in Docs
  - macOS text replacement is buggy and inconsistent
  - AutoHotkey/Espanso require technical configuration
  - EkaKey's auto-learning corrupts common words
- **10-20 predictable typos**: The user's typos are consistent and known, making manual rule definition feasible

### Target User
Fast typer with predictable patterns. Types quickly to capture ideas, primarily on a Windows PC with admin access. Comfortable editing text files for configuration. Personal use only.

### Success Criteria
- Type at full speed without breaking flow to fix predictable typos
- Zero unwanted corrections (user defines all rules)
- Invisible operation—no popups, no sounds, no interruptions
- Easy rule management via hotkey and text files

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Rule** | A typo-to-correction mapping (e.g., `teh=the`) stored in rules.txt |
| **Trigger** | The typo word that activates a correction (e.g., "teh") |
| **Correction** | The correct word that replaces the trigger (e.g., "the") |
| **Delimiter** | A character that marks word boundaries; in this app, only space |
| **Whole-word matching** | Correction only applies when trigger is a complete word, not part of another word |
| **Pattern suggestion** | A potential typo detected by the app (not in dictionary, typed 5+ times) |
| **Ignore list** | Words the user has marked to never suggest as potential typos |
| **Correction log** | Rolling log of the last 100 corrections made by the app |
| **Custom words** | User-defined words to add to the dictionary (names, jargon, etc.) |

---

## 3. Requirements

### REQ-1: Silent Typo Correction

**Traces to**: A1 (consistent typos), A2 (double interruption), A3 (silent correction), A9 (simple rules)

**User Story**: As a fast typer, I want my known typos automatically corrected as I type, so that I can maintain my writing flow without stopping to fix mistakes.

**Acceptance Criteria**:

1. THE System SHALL monitor keystrokes system-wide while running
2. THE System SHALL load correction rules from `rules.txt` on startup
3. THE System SHALL detect when a typed word matches a rule trigger followed by a space
4. THE System SHALL replace the trigger with its correction using backspace and retype
5. THE System SHALL only match whole words (e.g., "teh" in "Teheran" is NOT corrected)
6. THE System SHALL preserve the original casing pattern:
   - "teh" → "the" (lowercase)
   - "Teh" → "The" (capitalized)
   - "TEH" → "THE" (uppercase)
7. THE System SHALL NOT produce any visual or audio feedback when correcting
8. THE System SHALL support Ctrl+Z to undo corrections via native application undo

---

### REQ-2: Rule Management

**Traces to**: A5 (willing to define rules), A9 (simple rules sufficient)

**User Story**: As a user, I want to easily add and manage my correction rules, so that I can customize the app to my specific typo patterns.

**Acceptance Criteria**:

1. THE System SHALL store rules in `Documents/CustomAutocorrect/rules.txt`
2. THE System SHALL use the format `typo=correction` (one rule per line)
3. THE System SHALL support adding rules via the Win+Shift+A hotkey
4. THE System SHALL reload rules when the rules file is modified
5. THE System SHALL ignore blank lines and lines starting with `#` (comments)

---

### REQ-3: Password Field Protection

**Traces to**: A3 (silent correction), user security concern

**User Story**: As a user, I want the app to skip password fields, so that my passwords aren't accidentally modified.

**Acceptance Criteria**:

1. THE System SHALL attempt to detect password input fields
2. THE System SHALL NOT perform corrections in detected password fields
3. THE System SHALL use best-effort detection (may not catch all password fields)

---

### REQ-4: Pattern Suggestion

**Traces to**: A8 (pattern suggestion value)

**User Story**: As a user, I want the app to notice words I frequently mistype, so that I can discover typo patterns I wasn't aware of.

**Acceptance Criteria**:

1. THE System SHALL maintain a built-in English word list
2. THE System SHALL track words typed that are not in the dictionary or custom words
3. THE System SHALL log a word to `suggestions.txt` after it's typed 5 or more times
4. THE System SHALL NOT automatically create rules from suggestions
5. THE System SHALL NOT suggest words already in the ignore list
6. THE System SHALL allow users to add words to `custom-words.txt` to prevent false suggestions

---

### REQ-5: Ignore List Management

**Traces to**: A8 (pattern suggestion), user feedback on suggestion fatigue

**User Story**: As a user, I want to tell the app to stop suggesting certain words, so that I'm not repeatedly bothered by intentional non-dictionary words.

**Acceptance Criteria**:

1. THE System SHALL provide a tray menu option to view current suggestions
2. THE System SHALL provide a tray menu option to ignore a suggested word
3. THE System SHALL store ignored words in `ignore.txt`
4. THE System SHALL never suggest words present in `ignore.txt`

---

### REQ-6: Correction Logging

**Traces to**: A7 (system-wide reliability), user need for verification

**User Story**: As a user, I want to see a log of corrections the app has made, so that I can verify it's working correctly.

**Acceptance Criteria**:

1. THE System SHALL log each correction to `corrections.log`
2. THE System SHALL record: timestamp, original word, corrected word, active window title
3. THE System SHALL maintain a maximum of 100 log entries
4. THE System SHALL rotate out oldest entries when the limit is reached
5. THE System SHALL store the log in `Documents/CustomAutocorrect/`

---

### REQ-7: System Tray Integration

**Traces to**: A7 (system-wide works), MVP scope decision

**User Story**: As a user, I want a tray icon so I know the app is running and can access its features.

**Acceptance Criteria**:

1. THE System SHALL display an icon in the Windows system tray when running
2. THE System SHALL provide a right-click menu with options:
   - View Suggestions (shows suggestions.txt contents)
   - Ignore Suggestion (submenu or dialog)
   - Open Rules File
   - Open Corrections Log
   - Exit
3. THE System SHALL exit cleanly when "Exit" is selected

---

### REQ-8: Startup and Lifecycle

**Traces to**: A7 (system-wide works), technical decisions

**User Story**: As a user, I want the app to start automatically with Windows and run unobtrusively.

**Acceptance Criteria**:

1. THE System SHALL be packageable as a single Windows executable via PyInstaller
2. THE System SHALL support running from Windows Startup folder
3. THE System SHALL run as a background process with minimal resource usage
4. THE System SHALL create the `Documents/CustomAutocorrect/` folder if it doesn't exist
5. THE System SHALL create default empty files (rules.txt, etc.) if they don't exist

---

### REQ-9: File Storage

**Traces to**: Technical decisions, user preference for editable files

**User Story**: As a user, I want all app data stored in an accessible location, so that I can manually edit files when needed.

**Acceptance Criteria**:

1. THE System SHALL store all user files in `Documents/CustomAutocorrect/`
2. THE System SHALL use plain text formats for all files
3. THE System SHALL create and manage these files:
   - `rules.txt` - user-defined correction rules
   - `suggestions.txt` - detected potential typos
   - `ignore.txt` - words to never suggest
   - `corrections.log` - rolling log of corrections made
   - `custom-words.txt` - user additions to the dictionary

---

## 4. Out of Scope

The following are explicitly excluded from this project (per ideation decisions):

- **Auto-learning from user behavior** - No inferring rules from backspaces or edits
- **Phonetic matching / fuzzy correction** - Only exact rule matching
- **Complex suggestion UI** - Suggestions logged to file, not shown as popups
- **Cross-platform support** - Windows only for MVP
- **Installer** - Single .exe distribution only
- **Cloud sync** - Local files only
- **Multi-language support** - English dictionary only

---

## 5. File Format Specifications

### rules.txt
```
# Comment lines start with #
teh=the
adn=and
hte=the
```

### suggestions.txt
```
# Words typed 5+ times that aren't in dictionary
# Add to rules.txt to create a correction, or ignore via tray menu
adn (typed 7 times)
wiht (typed 5 times)
```

### ignore.txt
```
# Words to never suggest
GitHub
TypeScript
localhost
```

### corrections.log
```
2026-01-31 14:23:15 | teh → the | Chrome - Google Docs
2026-01-31 14:25:02 | adn → and | Notepad
```

### custom-words.txt
```
# Additional words to treat as valid (won't be suggested as typos)
GitHub
TypeScript
localhost
```
