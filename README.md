# Specola

**Your daily observatory on what matters.**

Specola is a native macOS menubar app that fetches your RSS feeds every morning, has Claude analyze and prioritize them based on your professional profile, and delivers a polished DOCX briefing — your personal intelligence report, ready before your first coffee.

The name comes from *specola*: the observatory tower from which astronomers scan the horizon.

---

## How It Works

```
    OPML feeds          Claude Code CLI           DOCX briefing
   ┌──────────┐        ┌──────────────┐        ┌──────────────┐
   │ 200+ RSS │───────▶│  AI analysis │───────▶│  Structured  │
   │  sources  │  fetch │  & ranking   │ render │   report     │
   └──────────┘        └──────────────┘        └──────────────┘
         │                     │                       │
         │              prioritized by            opens in Word,
     concurrent         your profile              Pages, or any
     fetching           and interests             DOCX reader
```

1. **You configure** your RSS feeds (OPML) and describe your professional profile
2. **Every day at your chosen time**, Specola fetches all feeds concurrently
3. **Claude Code CLI** analyzes the digest and produces a structured briefing tailored to you
4. **A DOCX file** lands in your Documents folder — ready to read, share, or archive

No API keys needed. No cloud service. Just the Claude Code CLI on your Mac.

## What You Get

Each briefing ("Specola") contains:

- **Da sapere oggi** — The 3-5 things that matter most for your profile
- **Richiede attenzione** — Developments that need action this week
- **Per area tematica** — Deep coverage by category, ranked by relevance
- **Da leggere con calma** — Long reads worth your time
- **Spunti** — Ideas for posts, reflections, or next moves

Everything sourced, nothing invented.

## Requirements

- **macOS 14 (Sonoma)** or later
- **Claude Code CLI** installed and working (`claude` in your PATH)
- **Python 3.9+** (ships with macOS or install via Homebrew)
- An **OPML file** with your RSS feeds

## Installation

```bash
# Clone the repository
git clone https://github.com/user/specola.git
cd specola

# Build the app
xcodebuild -project Specola.xcodeproj -scheme Specola -configuration Release build

# The engine sets itself up on first launch, or manually:
cd engine
./setup_engine.sh
```

Open the built app from Xcode's DerivedData, or run it directly from Xcode.

## Quick Start

1. **Launch Specola** — a binoculars icon appears in your menubar
2. **Open Settings** (click the icon, then "Impostazioni...")
3. **Import your OPML** file in the "Fonti" tab
4. **Write your profile** in the "Profilo" tab — describe your role, stack, interests
5. **Click "Genera ora"** to create your first briefing
6. The DOCX opens automatically. Tomorrow's will arrive on schedule.

## Architecture

Specola is two components talking via JSON over stdout:

### Swift App (UI + orchestration)

Native SwiftUI menubar app. Handles scheduling (60-second timer + wake-from-sleep detection), user settings, history tracking, and macOS notifications. No external Swift packages.

### Python Engine (the brain)

Standalone CLI that does the heavy lifting:

| Module | Role |
|--------|------|
| `feed_fetcher.py` | OPML parsing + concurrent RSS fetch (20 threads) |
| `prompt_builder.py` | Assembles the analysis prompt (IT/EN) |
| `analyzer.py` | Invokes `claude -p` via subprocess |
| `doc_generator.py` | Renders markdown to DOCX with python-docx |

```bash
# You can run the engine standalone
cd engine
.venv/bin/python specola_engine.py run \
    --opml ~/feeds.opml \
    --profile ~/profile.md \
    --output-dir ~/Documents/Specola \
    --language it
```

### Interface Contract

```
Swift → Python:  CLI arguments (--opml, --profile, --output-dir, --hours, --language)
Python → Swift:  JSON on stdout {"status": "ok", "output_path": "...", "feed_count": N, "item_count": N}
```

## Configuration

### Settings Tabs

| Tab | What it does |
|-----|-------------|
| **Fonti** | Import/remove OPML file, see feed count |
| **Pianificazione** | Set daily generation time, auto-generate toggle, launch at login |
| **Profilo** | Free-text description of your role, interests, and projects |
| **Avanzate** | Output directory, language (IT/EN), time window (6-72h), Claude CLI path |

### Data Storage

| What | Where |
|------|-------|
| Settings | `UserDefaults` (com.oltrematica.specola) |
| Profile | `~/Library/Application Support/Specola/profile.md` |
| OPML copy | `~/Library/Application Support/Specola/Feeds.opml` |
| History | `~/Library/Application Support/Specola/history.json` |
| Briefings | `~/Documents/Specola/Specola_YYYY-MM-DD.docx` |

## Engine CLI Reference

```
specola_engine.py run [options]

--opml PATH           OPML file path (required)
--profile PATH        User profile file (required)
--output-dir PATH     DOCX output directory (required)
--hours N             Time window in hours (default: 24)
--language it|en      Briefing language (default: it)
--max-items N         Max items per category (default: 30)
--model MODEL         Claude model override
--dry-run             Fetch only — no Claude, no DOCX
--verbose             DEBUG logging to stderr
```

## Development

```bash
# Python engine tests (44 tests)
cd engine
.venv/bin/python -m pytest tests/ -v

# Swift tests (15 tests)
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests \
    -destination 'platform=macOS' test

# Regenerate Xcode project after adding files
xcodegen generate
```

### Project Structure

```
specola/
├── Specola/                    # Swift app source
│   ├── SpecolaApp.swift        # @main entry, MenuBarExtra
│   ├── MenuBarView.swift       # Popover UI
│   ├── SettingsView.swift      # Four-tab settings
│   ├── Models/                 # SpecolaEntry, AppState, Settings
│   ├── Services/               # Engine, Scheduler, Notifications
│   └── Helpers/                # MenuBarIcon badge rendering
├── SpecolaTests/               # Swift unit tests
├── engine/                     # Python engine
│   ├── specola_engine.py       # CLI entry point
│   ├── src/                    # Core modules
│   └── tests/                  # pytest suite
├── project.yml                 # xcodegen spec
└── CLAUDE.md                   # AI assistant instructions
```

## Design Decisions

- **No API keys** — Uses Claude Code CLI (`claude -p`), not the Anthropic API
- **No Electron** — Native Swift/SwiftUI for a real Mac experience
- **No async Python** — ThreadPoolExecutor is simpler and sufficient for I/O-bound RSS fetching
- **No Core Data** — A JSON file handles 30 history entries just fine
- **No launchd** — Internal timer + wake detection keeps scheduling self-contained
- **DOCX, not PDF** — Editable, searchable, easy to share and annotate

## License

See [LICENSE](LICENSE).

---

*Built with Swift, Python, and Claude Code.*
