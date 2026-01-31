# CONVENTIONS

Claude: Read this before generating Python code, tests, or file operations.

## Python Naming

| Element | Convention | Example |
|---------|------------|---------|
| Functions | snake_case | `load_rules()`, `apply_correction()` |
| Variables | snake_case | `word_buffer`, `active_window` |
| Classes | PascalCase | `RuleEngine`, `CorrectionLogger` |
| Constants | UPPER_SNAKE | `MAX_LOG_ENTRIES = 100` |
| Files | snake_case | `rule_engine.py`, `correction_logger.py` |
| Test files | test_*.py | `test_rule_engine.py` |

## Project Structure

```
custom-autocorrect/
├── src/
│   └── custom_autocorrect/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── keyboard_hook.py     # Keystroke capture
│       ├── rule_engine.py       # Rule loading and matching
│       ├── correction.py        # Correction execution
│       ├── suggestion.py        # Pattern suggestion tracking
│       ├── tray.py              # System tray integration
│       ├── logger.py            # Correction logging
│       └── utils.py             # Shared utilities
├── tests/
│   ├── test_rule_engine.py
│   ├── test_correction.py
│   ├── test_suggestion.py
│   └── conftest.py              # pytest fixtures
├── resources/
│   └── words.txt                # English dictionary
├── requirements.txt
├── pyproject.toml
└── build.py                     # PyInstaller build script
```

## REQUIRED: Error Handling Pattern

```python
# DO: Return None or raise specific exceptions
def load_rules(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    # ...

# DO: Use specific exception types
class RuleParseError(Exception):
    pass

# NOT: Bare except or generic Exception
try:
    ...
except:  # NOT this
    pass
```

## REQUIRED: File Path Handling

```python
# DO: Use pathlib.Path, not string concatenation
from pathlib import Path

config_dir = Path.home() / "Documents" / "CustomAutocorrect"
rules_path = config_dir / "rules.txt"

# NOT: String concatenation
rules_path = os.path.join(os.environ["USERPROFILE"], "Documents\\CustomAutocorrect\\rules.txt")
```

## REQUIRED: Type Hints

```python
# DO: Add type hints to function signatures
def apply_casing(word: str, pattern: str) -> str:
    ...

def load_rules(path: Path) -> dict[str, str]:
    ...

# NOT: Untyped functions
def apply_casing(word, pattern):
    ...
```

## REQUIRED: Test Structure

```python
# DO: Descriptive test names, arrange-act-assert pattern
def test_casing_preserves_uppercase():
    # Arrange
    correction = "the"
    trigger = "TEH"

    # Act
    result = apply_casing(correction, trigger)

    # Assert
    assert result == "THE"

# DO: Use pytest fixtures for shared setup
@pytest.fixture
def sample_rules():
    return {"teh": "the", "adn": "and"}

def test_rule_lookup_case_insensitive(sample_rules):
    engine = RuleEngine(sample_rules)
    assert engine.lookup("TEH") == "the"
```

## REQUIRED: Docstrings for Public Functions

```python
# DO: Brief docstring for public functions
def apply_correction(trigger: str, correction: str) -> None:
    """Replace the just-typed trigger with the correction via backspace+retype."""
    ...

# NOT: No docstring or overly verbose
def apply_correction(trigger, correction):
    # This function takes a trigger and correction and replaces...
    ...
```

## Constants

```python
# Define in module where used, or in a constants.py if shared

# File locations
CONFIG_DIR_NAME = "CustomAutocorrect"
RULES_FILE = "rules.txt"
SUGGESTIONS_FILE = "suggestions.txt"
IGNORE_FILE = "ignore.txt"
CORRECTIONS_LOG = "corrections.log"
CUSTOM_WORDS_FILE = "custom-words.txt"

# Limits
MAX_LOG_ENTRIES = 100
SUGGESTION_THRESHOLD = 5
```

## Logging (Debug Output)

```python
# DO: Use logging module, not print statements
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Loaded {len(rules)} rules")
logger.warning(f"Could not parse rule: {line}")

# NOT: print() for debugging
print(f"Loaded {len(rules)} rules")
```
