# Specola — Design Spec

> macOS menubar app that generates daily RSS briefings analyzed by Claude Code CLI, output as DOCX.

## Overview

Specola fetches RSS feeds from an OPML file, has Claude Code CLI analyze and prioritize them based on the user's professional profile, and produces a structured DOCX briefing ("Specola"). It runs daily at a user-configured time, lives in the macOS menubar, and requires no API keys — only the Claude Code CLI installed on the machine.

## Architecture

Two independent components communicating via Process/stdout JSON:

```
┌─────────────────────┐         CLI args           ┌─────────────────────┐
│   Swift App (UI)    │ ──────────────────────────▶│   Python Engine     │
│                     │                            │                     │
│  - Menubar + badge  │         JSON stdout        │  - Feed fetching    │
│  - Popover          │ ◀──────────────────────────│  - Claude CLI call  │
│  - Settings         │                            │  - DOCX generation  │
│  - Scheduling       │         stderr (logs)      │                     │
│  - Notifications    │ ◀──────────────────────────│                     │
└─────────────────────┘                            └─────────────────────┘
```

**Interface contract:**

- Swift → Python: CLI arguments (`--opml`, `--profile`, `--output-dir`, `--hours`, `--language`)
- Python → Swift: JSON on stdout

```json
// Success
{"status": "ok", "output_path": "/path/to/Specola_2026-04-05.docx", "feed_count": 187, "item_count": 42}

// Error
{"status": "error", "message": "Claude CLI non trovata"}
```

No bidirectional communication, no sockets, no shared intermediate files.

## Implementation Strategy

**Engine Python first.** The engine is self-contained and testable from CLI without any UI. Once validated end-to-end, the Swift app wraps it with scheduling and UI.

---

## Python Engine

### Stack

- Python 3.12+
- Dependencies: `feedparser`, `python-docx`, `python-dateutil`
- Entry point: `engine/specola_engine.py`
- Modules: `engine/src/`

### Structure

```
engine/
├── specola_engine.py       # Entry point, argparse, orchestration
├── requirements.txt        # feedparser, python-docx, python-dateutil
├── setup_engine.sh         # Creates venv, installs deps
├── src/
│   ├── __init__.py
│   ├── feed_fetcher.py     # OPML parsing + concurrent RSS fetch
│   ├── analyzer.py         # Claude CLI invocation via subprocess
│   ├── doc_generator.py    # DOCX generation with python-docx
│   └── prompt_builder.py   # Dynamic prompt construction
└── .work/                  # Intermediate files (created at runtime)
```

### CLI

```
specola_engine.py run [options]

--opml PATH              OPML file path
--profile PATH           User profile file (profile.md)
--output-dir PATH        DOCX output directory
--hours N                Time window in hours (default: 24)
--language LANG          Briefing language: it/en (default: it)
--max-items N            Max items per category (default: 30)
--model MODEL            Model for synthesis (phase 2). Also used for categories if --category-model not set.
--category-model MODEL   Faster/cheaper model for per-category analysis (phase 1). Falls back to --model.
--dry-run                Fetch only, no Claude, no DOCX
--verbose                DEBUG logging
```

Output: JSON on stdout. Logging on stderr.

### Module Responsibilities

| Module | Input | Output |
|--------|-------|--------|
| `feed_fetcher.py` | OPML path, hours, max_items | `dict[str, list[FeedItem]]` (category → items) |
| `prompt_builder.py` | profile text, language, categories list | Complete prompt string |
| `analyzer.py` | digest file path, prompt, model, timeout | Markdown string or None |
| `doc_generator.py` | markdown text, date, output_dir | DOCX file path |

### Orchestration Flow (specola_engine.py)

1. Parse OPML → concurrent RSS fetch (ThreadPoolExecutor, 20 workers)
2. Filter items by time window → generate markdown digest → save to `.work/`
3. Build prompt (system instruction + user profile + output instructions)
4. Invoke `claude -p "prompt" < digest.md` via subprocess (timeout: 300s)
5. Parse markdown output → generate DOCX with python-docx
6. If Claude fails → fallback DOCX from raw digest with red warning paragraph
7. Print JSON result to stdout

### Feed Fetcher Details

**OPML parsing:**
- `xml.etree.ElementTree`
- First-level `<outline>` = category
- Children with `type="rss"` = feed
- Strip numeric prefixes ("01 – " → "")
- Ordered dict by name

**RSS fetching:**
- `feedparser.parse(url)` with User-Agent `"Specola/1.0"`
- `ThreadPoolExecutor`, max 20 workers
- 15 second timeout per feed
- Failed feeds: debug log to stderr, no fatal error
- Filter: only items within last N hours (timezone-aware UTC)
- Date resolution: `published_parsed` → `updated_parsed` → `dateutil.parser.parse`
- Undetermined date: include the item
- Summary: `entry.summary` → `entry.description` → `entry.content[0].value`
- Strip HTML: regex `<[^>]+>`, `html.unescape()`, collapse whitespace
- Truncate summary to 500 characters
- Max N items per category, sorted by date descending

**FeedItem structure:**

```python
{"title": str, "link": str, "published": str, "summary": str, "source": str}
```

### Prompt Builder

Three parts assembled:

1. **System instruction** (fixed): "Sei Specola, un assistente che produce briefing giornalieri da fonti RSS..."
2. **User profile** (from profile.md, injected verbatim)
3. **Output instructions** (language-dependent, hardcoded constants for `it` and `en`)

Output structure (both languages):
- Da sapere oggi / Must know today (3-5 bullet points)
- Richiede attenzione / Needs attention (actionable items)
- Per area tematica / By topic (category sections, items by relevance)
- Da leggere con calma / Deep reads
- Spunti / Ideas

Rules: no fluff, source attribution in parentheses, omit empty sections, max 3000 words.

Appended: list of categories present in the digest.

### Analyzer

Exact pattern, no retry, no backoff:

```python
def analyze_with_claude(digest_path, prompt, model=None, timeout=300):
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])
    with open(digest_path, "r") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        return None
    return result.stdout
```

If `claude` not in PATH: return JSON error. If fails: fallback DOCX from raw digest.

### DOCX Generation

python-docx formatting:

- A4, 2.5cm margins
- Calibri 11pt, line spacing 1.15
- H1: 18pt bold #1a1a2e, spacing before 18pt after 6pt
- H2: 14pt bold #16213e, spacing before 14pt after 4pt
- H3: 12pt bold #0f3460, spacing before 10pt after 4pt
- Paragraphs: spacing after 6pt
- Header: "Specola" left, date right, 9pt grey
- Footer: page number centered, 9pt grey
- Filename: `Specola_YYYY-MM-DD.docx`

Markdown → DOCX line-by-line with regex:
- `# ` → Heading 1, `## ` → Heading 2, `### ` → Heading 3
- `- ` / `* ` → List Bullet
- `**text**` → bold run
- `1. ` → List Number
- Empty lines → separator
- Everything else → paragraph

No markdown parsing libraries. Fallback: DOCX from raw digest with red "⚠ Analisi non disponibile." paragraph.

---

## Swift App

### Technology

- Swift 5.9+, SwiftUI
- Target: macOS 14 (Sonoma)+
- Xcode project, no external SPM packages unless strictly necessary
- App sandbox: disabled (must invoke external processes: python, claude)
- LSUIElement = true (no dock icon, menubar only)
- Login item: option in settings

### Menubar

- Icon: SF Symbol `binoculars`
- Badge: numeric counter overlay top-right (Mail.app style)
- Counter shows unread Specole count; hidden when 0
- Click: opens popover

### Popover

Top to bottom:

1. **Header**: bold "Specola" title + subtitle with last generation date/time
2. **List**: last 10 Specole, sorted by date descending. Each row: date, feed count, unread indicator (blue dot). Click → opens DOCX via `NSWorkspace.shared.open()` and marks as read.
3. **Actions**: "Genera ora" button. During generation: indeterminate progress bar with "Generazione in corso...". Disabled during generation.
4. **Footer**: "Impostazioni..." (opens Settings window), "Esci" (quits app)

### Settings Window

Separate window (not in popover), macOS standard style. **TabView** with 4 tabs:

**Fonti:**
- Label showing current OPML path (or "Nessun file OPML configurato")
- "Scegli file OPML..." button → NSOpenPanel, filter .opml/.xml
- "Rimuovi" button → removes OPML reference
- After selection: summary (N categories, M total feeds) from OPML parsing
- OPML file copied to `Application Support/Specola/Feeds.opml`

**Pianificazione:**
- Time picker hours/minutes (default: 07:00)
- Checkbox "Genera automaticamente" (default: on)
- Note: "Se il Mac è in stop all'orario previsto, la Specola verrà generata al risveglio."
- Checkbox "Avvia Specola al login" (manages Login Item)

**Profilo:**
- Label with instructions
- Multiline TextEditor, min height 200pt, resizable
- Placeholder text with example
- No character limit. Saved verbatim.
- Auto-save on focus loss (no explicit save button needed)

**Avanzate:**
- DOCX output directory (default: `~/Documents/Specola/`)
- "Apri cartella" button
- Language: segmented control "Italiano" / "English" (default: Italiano)
- Time window: stepper "Ultime N ore" (default: 24, min: 6, max: 72)
- Claude Code CLI path (auto-detected, manual override possible)

### Persistence

| Data | Storage | Path |
|------|---------|------|
| Schedule time, language, hours, output path | UserDefaults | — |
| User profile | File | `Application Support/Specola/profile.md` |
| OPML (copy) | File | `Application Support/Specola/Feeds.opml` |
| Specola history | JSON | `Application Support/Specola/history.json` |
| Generated DOCX | Files | `~/Documents/Specola/Specola_YYYY-MM-DD.docx` |
| Engine + venv | Directory | `Application Support/Specola/engine/` |

**history.json:** Array of entries, max 30, FIFO. DOCX files not deleted on removal from history.

```json
[{"id": "2026-04-05", "date": "2026-04-05T07:00:00Z", "path": "...", "feedCount": 187, "itemCount": 42, "read": false}]
```

### Scheduling

Internal to the app, no launchd:

- Timer every 60 seconds checks if generation is due
- Condition: current time >= configured time AND no Specola generated today (check history.json)
- Wake-from-sleep (`NSWorkspace.didWakeNotification`): immediately check if today's Specola exists; if not and time has passed, trigger generation
- Generation runs in async Task, does not block UI
- On completion: add entry to history.json, update badge counter, show native macOS notification

### Engine Invocation

```swift
let process = Process()
process.executableURL = URL(fileURLWithPath: pythonPath) // .venv/bin/python
process.arguments = [enginePath, "run",
    "--opml", opmlPath, "--profile", profilePath,
    "--output-dir", outputDir, "--hours", String(hours), "--language", language]
process.currentDirectoryURL = engineDir
```

Parse stdout JSON to update app state.

### First Launch

1. Check if Python venv exists at `Application Support/Specola/engine/.venv/`
2. If not: copy bundled `engine/` directory, run `setup_engine.sh`
3. Check if `claude` is in PATH (`/usr/local/bin/claude`, `~/.local/bin/claude`, `~/.claude/local/claude`, system PATH)
4. If `claude` not found: show alert with install instructions, don't block app
5. Open Settings window automatically
6. "Genera ora" disabled until OPML is configured

### Notifications

- `UNUserNotificationCenter`
- On success: "Specola del [date] pronta — N articoli analizzati" with "Apri" action
- On error: "Specola: generazione fallita" with error message in body
- Request notification permission on first launch

---

## File Structure

```
Specola/
├── Specola.xcodeproj
├── Specola/
│   ├── SpecolaApp.swift
│   ├── MenuBarView.swift
│   ├── SettingsView.swift
│   ├── Models/
│   │   ├── SpecolaEntry.swift
│   │   ├── AppState.swift
│   │   └── Settings.swift
│   ├── Services/
│   │   ├── EngineService.swift
│   │   ├── SchedulerService.swift
│   │   └── NotificationService.swift
│   ├── Assets.xcassets
│   └── Info.plist
├── engine/
│   ├── specola_engine.py
│   ├── requirements.txt
│   ├── setup_engine.sh
│   └── src/
│       ├── __init__.py
│       ├── feed_fetcher.py
│       ├── analyzer.py
│       ├── doc_generator.py
│       └── prompt_builder.py
├── CLAUDE.md
└── README.md
```

## Constraints

- No Electron, Tauri, or web wrappers
- No SwiftPM packages for RSS
- No `click`, `typer`, `rich`, `colorama` in Python engine
- No retry or exponential backoff
- No web scraping (RSS only)
- No async/await in Python (threads suffice)
- No `import anthropic` or direct API calls
- No template engines (Jinja, Mako) for prompts
- No Core Data (JSON suffices)
- No launchd for scheduling
- No DMG or installer — build from Xcode

## Design Decisions

- **Menubar icon**: SF Symbol `binoculars` — directly evokes the "specola" (observatory) concept
- **Settings layout**: TabView with 4 tabs — classic macOS pattern, gives the Profile TextEditor adequate space
- **Implementation order**: Engine Python first — self-contained, testable from CLI, validates the core value proposition before building UI
