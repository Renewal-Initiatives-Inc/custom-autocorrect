# Ideation: Custom Autocorrect

## Meta
- Status: Ready for Kickoff
- Last Updated: 2026-01-31
- Sessions: 3

## 1. Origin
- **Entry Type**: Problem
- **Initial Statement**: "An autocorrection system that lets you choose what words you want to autocorrect, from one thing into another. When I type fast, I mistype a lot, such as 'teh' instead of 'the' and I'd like this app to autodetect my most common mistakes and just autocorrect them, rather than having the red squiggly lines telling me it's a mistake—I know that! Just correct it."
- **Refined Problem Statement**: When typing quickly, the user consistently makes the same 10-20 typos. Current spellcheck solutions only highlight errors (red squiggly) rather than silently fixing them. The user wants automatic, silent correction of their personal typo patterns—no interruption, no confirmation, just fixed.

## 2. Jobs to be Done
- **Primary Job**: Type at full speed without breaking flow to fix predictable typos
- **Related Jobs**:
  - Maintain writing quality without manual proofreading
  - Build a personalized dictionary of common mistakes over time
  - Reduce cognitive load and frustration while typing
- **Current Alternatives**:
  - Google Docs: Tools → Preferences → Substitutions (works well, but only in Docs)
  - macOS Text Replacement: Inconsistent, many apps don't support it
  - Browser extensions: Not available on locked-down Chromebook
  - Manual correction: Delete, retype, continue (current painful workflow)
- **Switching Triggers**:
  - Frustration threshold reached after repeatedly fixing the same typos
  - Deadline pressure when typing speed matters most
  - Discovery that a simple solution exists

## 3. User Segments

### Segment 1: Fast Typer with Predictable Patterns (Primary - The User)
- **Context**: Student working on school assignments, primarily in Google Docs and web forms. Types fast to capture ideas. Uses Chromebook (no admin) and Windows PC (has admin).
- **Motivation**: Stop the double-interruption of noticing a typo AND fixing it. Just keep the flow going.
- **Ability Barriers**:
  - Chromebook: No admin privileges, cannot install extensions
  - Cross-platform: Needs solution that works on multiple devices
  - Setup friction: Willing to define 10-20 rules, but not hundreds
- **Potential Prompts**:
  - Typing an essay under deadline
  - Noticing the same typo for the 50th time
  - Submitting something with an embarrassing typo

### Segment 2: Power User / Developer (Potential)
- **Context**: Types across many apps—IDE, terminal, Slack, email. Wants consistency everywhere.
- **Motivation**: System-wide muscle memory. Same corrections everywhere.
- **Ability Barriers**: Willing to configure, but wants it to "just work" after setup
- **Potential Prompts**: Switching to a new machine and realizing all customizations are lost

## 4. Market Landscape

### Direct Competitors

| Competitor | What They Do | Strengths | Weaknesses | Pricing |
|------------|--------------|-----------|------------|---------|
| **AutoHotkey + AutoCorrect Script** | Windows automation with community autocorrect script (4,000+ words) | Free, system-wide, highly customizable, Win+H to add words | Windows only, requires running script, intimidating for non-technical users | Free |
| **Espanso** | Cross-platform text expander with autocorrect packages | Free, open-source, works on Win/Mac/Linux, YAML config, active development | Requires manual YAML editing, no pattern detection, learning curve | Free |
| **EkaKey** | Flutter-based Windows autocorrect with ML learning | System-wide, learns from corrections, phonetic matching, nice UI | Brand new (Dec 2025), Windows only, unproven stability, 8 commits total | Free |
| **PhraseExpress** | Feature-rich text expander and autocorrect | Imports MS Office autocorrect, system-wide, cloud sync | Nag screens on free version, complex UI, overkill for simple typo fixing | Free (limited) / $30-50 |
| **Breevy** | Simple Windows text expander | Clean UI, stable, imports MS Office autocorrect, one-time purchase | Windows only, no learning/pattern detection, paid only | $24/yr or $99 lifetime |
| **FastKeys** | All-in-one Windows automation | Lightweight, cheap, includes autocorrect | Windows only, less focused on autocorrect specifically | ~$10 |
| **Lightkey** | AI predictive typing | Predicts words as you type, 85 languages | More prediction than correction, Windows only, learning curve | Freemium |
| **TextHelp AutoCorrect** | Enterprise/education autocorrect | Phonetic analysis, truly intelligent, system-wide | Enterprise pricing, not for individual consumers | Enterprise |

### Indirect Competitors

| Solution | How It's Used for This Job | Gap It Leaves |
|----------|---------------------------|---------------|
| **Grammarly** | Browser extension catches typos | Only works in browser, causes typing lag, focuses on grammar over typos, subscription model |
| **LanguageTool** | Similar to Grammarly | Browser-focused, grammar over simple typos |
| **Google Docs Substitutions** | Manual typo rules in Docs | Only works in Google Docs, not system-wide |
| **macOS Text Replacement** | System-level substitutions | Many apps ignore it, buggy, no pattern detection |
| **MS Word AutoCorrect** | Built-in Office autocorrect | Only works in Office apps |

### Market Signals

- **Reddit requests exist**: Multiple posts asking for "system-wide autocorrect for Windows" with no satisfying answers
- **EkaKey emergence**: New project (Dec 2025) with 96 GitHub stars suggests demand
- **Text expander market growing**: Tools like Espanso, TextExpander continue active development
- **No dominant solution**: Unlike mobile (built-in keyboards), desktop lacks a default autocorrect standard

### Opportunity Gaps

1. **No pattern detection**: Every tool requires manual rule setup. No tool watches your typing and suggests "you typed 'teh' 8 times—add a rule?"
2. **Setup friction**: AutoHotkey/Espanso are powerful but intimidating. Non-technical users bounce off YAML configs and .ahk scripts
3. **Cross-platform gap**: Espanso works cross-platform but your rules don't sync between machines easily
4. **"Just works" gap**: No tool offers a dead-simple "type your typos, we'll fix them" experience with zero config files

## 5. Assumptions Log

| ID | Assumption | Category | Importance | Confidence | Evidence | Validation Strategy |
|----|------------|----------|------------|------------|----------|---------------------|
| A1 | Users have 10-20 consistent typos, not random errors | Problem | High | High | User confirmed: "about 10-20 words I constantly mistype. It isn't that random." | Already validated |
| A2 | The "double interruption" (notice typo + fix it) breaks flow enough to seek a solution | Problem | High | High | User described painful workflow of deleting/retyping | Already validated |
| A3 | Silent correction is preferred over confirmation dialogs or suggestions | Problem | High | High | User explicitly said "silently start fixing things" | Already validated |
| A4 | Primary user is a fast typer who prioritizes flow over stopping to correct | User | Medium | High | User profile: types fast to "get ideas down onto paper" | Already validated |
| A5 | Users are willing to manually define 10-20 initial rules | User | High | Medium | User said yes, but real-world friction may differ | Test with prototype |
| A6 | There's a broader market beyond this single user | Market | Medium | Low | Reddit posts suggest demand, but unclear market size | Research communities, surveys |
| A7 | A system-wide Windows solution can work reliably across all apps | Solution | High | Medium | AutoHotkey/Espanso/EkaKey prove it's possible, but edge cases exist | Build MVP, test across apps |
| A8 | Pattern **suggestion** ("you've typed 'teh' 5 times—add rule?") adds value | Solution | Medium | Medium | User liked the idea but wants to confirm rules, not auto-learn | Prototype and observe usage |
| A9 | Simple manual rule setup (teh → the) is sufficient for MVP | Solution | High | High | Core use case is 10-20 known typos, not discovery | Build MVP with just this |
| A10 | Existing tools (Espanso, AutoHotkey) are too complex for average users | Market | High | Low | They work well for technical users; unclear if UX is the barrier | User testing with non-technical users |
| A11 | EkaKey hasn't captured the market—opportunity still exists | Market | High | Low | Only 96 stars, 8 commits; may be too new or may be perfect already | Test EkaKey, identify gaps |

### Priority Matrix

- **Test First** (High Importance, Low Confidence): A6, A10, A11
  - *These determine if building something new is worth it vs. just using EkaKey/Espanso*
- **Monitor** (High Importance, High Confidence): A1, A2, A3, A9
  - *Core problem validated; watch for changes*
- **Validate Later** (Medium/Lower Priority): A4, A5, A8
  - *Nice-to-haves and secondary features*
- **Build to Learn** (High Importance, Medium Confidence): A7
  - *Only way to validate is to build and test*

### Scope Decisions (from user feedback)

**IN SCOPE:**
- Manual rule definition (user explicitly adds `teh → the`)
- Silent, automatic correction based on defined rules
- Pattern suggestions ("you typed 'adn' 5 times—add a rule?") with user confirmation
- Simple rule management UI or hotkey

**OUT OF SCOPE (explicitly rejected):**
- Auto-learning from user behavior (backspaces, edits, etc.)
- Phonetic matching / fuzzy correction
- Complex suggestion UI
- Any feature that might interfere with the cognitive flow of typing

**Rationale:** "Typing ideas out is actually part of a really complex system of thinking... I don't want to overcomplicate what this tool actually does."

## 6. Solution Hypotheses

### Hypothesis 1: "Bare Bones"
- **Description**: Absolute minimum viable product. Background process watches keystrokes, reads rules from `rules.txt` (format: `teh=the`), corrects on Space via backspace+retype. No UI—edit the text file directly.
- **Key Differentiator**: Simplicity. Could be ~50-100 lines of code.
- **Target Segment**: The user (you)—someone comfortable editing a text file.
- **Validates Assumptions**: A7 (system-wide works), A9 (simple rules are enough)
- **Key Risks**: Too minimal—no way to quickly add rules while typing.
- **Prior Art**: py-ahk-abbr (Python AutoHotkey clone), various pynput tutorials.

### Hypothesis 2: "Smart Tracker" ⭐ (Recommended)
- **Description**: Bare Bones core + passive pattern logging. Two files: `rules.txt` (active corrections) and `suggestions.txt` (auto-logged frequent potential typos). Hotkey (Win+A) to quickly add current word as a rule. Optional tray icon in v1.1.
- **Key Differentiator**: Grows with you—passive logging surfaces patterns you might miss, but never auto-applies.
- **Target Segment**: The user (you)—wants simplicity but also a path to improvement.
- **Validates Assumptions**: A7 (system-wide works), A8 (pattern suggestion has value), A9 (simple rules work)
- **Key Risks**: Passive logging adds ~50 lines of complexity. Must ensure suggestions never auto-apply.
- **Prior Art**: No direct equivalent—most tools either auto-learn (risky) or don't track patterns at all.

### Hypothesis 3: "Desktop App"
- **Description**: Full application with settings window, tray icon, rule editor UI, import/export, stats dashboard.
- **Key Differentiator**: Polished experience, no text file editing.
- **Target Segment**: Non-technical users who want GUI.
- **Validates Assumptions**: A5 (willing to define rules), A7, A8
- **Key Risks**: Scope creep. Delays getting to a working solution. Overkill for personal use.
- **Prior Art**: EkaKey (Flutter), PhraseExpress, Breevy.

### Recommendation

**Pursue Hypothesis 2 ("Smart Tracker")** because:
1. Minimal core solves the immediate problem (A9 validated)
2. Passive logging tests pattern suggestion value (A8) without risk
3. Hotkey for quick rule addition reduces friction vs. pure text file
4. Clear upgrade path: add tray icon, then UI, as needed

**Key risks to monitor:**
- Ensure suggestions.txt never auto-applies rules
- Test across multiple apps (Chrome, Notepad, etc.) to validate A7

**Critical assumptions to validate early:**
- A7: System-wide Windows solution works reliably across all apps
- A9: Simple manual rules are sufficient (no phonetics needed)

## 7. Open Questions for /kickoff

### Requirements Questions
- [ ] What word delimiters trigger correction? (Space only, or also punctuation like `.`, `,`, `?`)
- [ ] Should corrections work in password fields? (Privacy concern)
- [ ] What happens if user types a rule's trigger inside another word? (e.g., "teh" inside "Teheran")
- [ ] How should casing be handled? ("Teh" → "The" or "the"?)
- [ ] What's the hotkey for adding rules? (Win+A? Configurable?)

### Technical Questions
- [ ] Python with `keyboard` library or `pynput`? (Need to test which works better)
- [ ] How to run on Windows startup? (Startup folder, registry, or scheduled task?)
- [ ] How to package for distribution? (PyInstaller, cx_Freeze, or just run as script?)
- [ ] Where to store rules.txt and suggestions.txt? (App folder, user's Documents, AppData?)

### Scope Questions
- [ ] Is pattern logging (suggestions.txt) in v1.0 or v1.1?
- [ ] Is tray icon in v1.0 or v1.1?
- [ ] What's the MVP feature set vs. "nice to have later"?

### User Experience Questions
- [ ] Should there be any visual feedback when a correction happens? (Brief flash? Sound? Nothing?)
- [ ] How to handle the "undo" case? (User corrects something they didn't want corrected)

## 8. Research Log
| Date | Topic | Source | Key Findings |
|------|-------|--------|--------------|
| 2026-01-31 | Landscape scan | Brave Search | Text expanders (aText, Espanso, TextExpander) focus on abbreviation→expansion, not typo correction. Most require manual rule setup. Asutype claims to learn patterns but is Windows-only and dated. |
| 2026-01-31 | Built-in solutions | Google Support, Brave Search | Google Docs has Tools→Preferences→Substitutions which handles the Docs use case. macOS has system text replacement but it's buggy and inconsistent across apps. |
| 2026-01-31 | User sentiment | Reddit r/MacOS, r/software | People frustrated with macOS text replacement not working in many apps (Word, Sublime, Chrome). Requests for "system-wide AI autocorrect" exist but no good solutions. |
| 2026-01-31 | AutoHotkey deep dive | GitHub, AutoHotkey.com | Mature autocorrect script with 4,000+ words. Win+H adds new words. Community-maintained. Requires running .ahk script at startup. |
| 2026-01-31 | Espanso analysis | GitHub, Reddit r/espanso, XDA | Cross-platform, Rust-based, YAML config. Has autocorrect packages. Users report occasional glitches with some apps. Very active development. |
| 2026-01-31 | EkaKey discovery | GitHub | New project (Dec 2025). Flutter + C++ hooks. Claims ML learning from corrections. Phonetic matching. Only 8 commits but 96 stars. Closest to our vision. |
| 2026-01-31 | Competitive pricing | Brave Search | Espanso/AutoHotkey = free. PhraseExpress = free w/nags or $30-50. Breevy = $24/yr or $99 lifetime. FastKeys = ~$10. |
| 2026-01-31 | Espanso vs AHK | Reddit, AlternativeTo | AHK more powerful/flexible but Windows-only. Espanso simpler for text expansion, cross-platform. Both require manual config. |
| 2026-01-31 | Grammarly issues | Reddit, GitHub | Causes typing lag. Users report slowdowns in Word/browser. More grammar than typo focused. |
| 2026-01-31 | Pattern detection search | Brave Search | TextHelp AutoCorrect (enterprise) and Lightkey (predictive) have some intelligence. No consumer tool auto-detects typo patterns. |
| 2026-01-31 | EkaKey creator research | GitHub profile | Creator is a high school student in India; EkaKey is first project. 96 stars but only 8 commits. Developer unavailable for 3 months due to exams. |
| 2026-01-31 | EkaKey bug analysis | GitHub Issues #3 | "Not ready for production" — aggressive learning corrupts common words. Root cause: auto-learning from backspaces infers wrong intent. |
| 2026-01-31 | EkaKey architecture deep dive | GitHub codebase | 3-layer architecture (C++ hooks → Dart logic → Flutter UI). 1,164 lines of core logic. Uses Double Metaphone for phonetics, Trie for suggestions, SQLite for storage. Key insight: complexity of state tracking across word boundaries causes bugs. |
| 2026-01-31 | Prior attempts - Python autocorrect | GitHub, PyPI, Medium | boppreh/keyboard library enables pure Python global hooks. py-ahk-abbr implements AHK-style expansion with pynput. Multiple tutorials confirm backspace+retype mechanism works. Core implementation is ~100 lines. |

## 9. Environment Constraints
| Environment | Admin Access | Extension Access | Status |
|-------------|--------------|------------------|--------|
| Chromebook + Google Docs | No | No | ✅ Solved via Substitutions |
| Chromebook + Web Forms | No | No | ❌ No viable solution |
| Windows PC | Yes | Yes | ✅ Solvable (AutoHotkey, Espanso, or custom) |

## 10. Partial Solution Implemented
**Google Docs Autocorrect** (completed during ideation):
- Tools → Preferences → Substitutions
- User to add their 10-20 common typos
- Works immediately, solves the primary use case on Chromebook

## 11. Learnings from EkaKey Analysis

### What EkaKey Got Right
1. **System-wide keyboard capture is feasible** — Low-level OS hooks can intercept keystrokes across all apps
2. **Silent correction works** — Backspace + retype is an effective correction mechanism
3. **User corrections should take priority** — Check user-defined rules before any algorithmic matching
4. **Casing preservation matters** — If user types "Teh", correct to "The" not "the"

### What EkaKey Got Wrong (Design Anti-Patterns)
1. **Auto-learning from backspaces** — The system tried to infer user intent from backspace behavior, leading to corrupted rules ("I" → "yiam"). Typing involves complex cognition; inferring intent from backspaces is unreliable.
2. **State machine complexity** — Tracking "edit mode" across word boundaries created edge cases that caused bugs
3. **Identity mappings as workaround** — Saving `word → word` to prevent re-correction is a hack that can corrupt common words
4. **Overly aggressive correction** — Applying corrections without user confirmation led to chaos

### Design Principles for Our App

| Principle | Rationale |
|-----------|-----------|
| **User confirms all rules** | Never auto-create rules. Suggest patterns, but user must approve. |
| **Simple rule engine** | Just a lookup table: `typo → correction`. No phonetics, no ML, no inference. |
| **Minimal state** | Track only the current word buffer. Don't track edit history or word chains. |
| **Fail safe** | If uncertain, do nothing. A missed correction is better than a wrong one. |
| **Respect cognitive flow** | Typing is thinking. The tool should be invisible, not intrusive. |

### Feature Risk Assessment

| Feature | Risk | Recommendation |
|---------|------|----------------|
| Manual rules (`teh → the`) | Low | ✅ Core feature—simple and safe |
| Silent correction (backspace + retype) | Low | ✅ Proven mechanism |
| Hotkey to add rules | Low | ✅ User-initiated, explicit |
| Pattern suggestion ("you typed X 5 times") | Medium | ⚠️ Nice-to-have; requires keystroke logging |
| Auto-learning from behavior | **High** | ❌ Avoid—caused EkaKey's critical bugs |
| Phonetic matching | Medium | ⚠️ Defer—adds complexity, marginal value for 10-20 known typos |
| Suggestion UI | Low | ⚠️ Optional—user prefers silent operation |
