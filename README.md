# Specola

**Your daily observatory on what matters.**

Specola is a native macOS menubar app that fetches your RSS feeds every morning, has your AI of choice analyze and prioritize them based on your professional profile, and delivers a polished briefing in your chosen format (DOCX, PDF, or EPUB) — your personal intelligence report, ready before your first coffee. Every briefing is also published as a standalone HTML page in a browsable portal archive, and today's highlights appear in a Notification Center widget.

Choose your LLM backend: **Claude Code CLI** for zero-config local analysis, **OpenAI API** for GPT-4o and beyond, or **LM Studio** for fully offline analysis with your own local models.

The name comes from *specola*: the observatory tower from which astronomers scan the horizon.

---

## How It Works

```
    OPML feeds       Your choice of AI         Your briefing
   ┌──────────┐     ┌──────────────────┐     ┌──────────────┐
   │ 200+ RSS │────▶│  Claude CLI      │────▶│  DOCX / PDF  │
   │  sources  │     │  OpenAI API      │     │  / EPUB      │
   └──────────┘     │  LM Studio       │     └──────────────┘
         │          └──────────────────┘       + HTML portal
     concurrent       prioritized by           + NC widget
     fetching         your profile             + standalone HTML
```

1. **You configure** your RSS feeds (OPML file), describe your professional profile, and pick your LLM provider
2. **Every day at your chosen time**, Specola fetches all feeds concurrently (up to 20 threads)
3. **Your chosen AI** — Claude Code CLI, OpenAI, or a local model via LM Studio — analyzes the full digest and produces a deep, structured briefing tailored to your role, stack, and interests
4. **A premium report** (DOCX, PDF, or EPUB — your choice) lands in your Documents folder — professionally formatted, with clickable source links, ready to read, share, or archive
5. **An HTML portal** is always generated alongside — a browsable archive of all your briefings, openable in any browser
6. **A Notification Center widget** shows today's key highlights at a glance

Works fully offline with LM Studio. Or use Claude/OpenAI for cloud-grade analysis. Your data, your choice.

---

## What You Get

Each briefing ("Specola") is a multi-page document with in-depth analysis, not a superficial summary. Every item includes a clickable link to the original source.

### Briefing Structure

| Section | What's inside |
|---------|--------------|
| **Da sapere oggi** | 5-7 key developments with context, implications, and source links |
| **Richiede attenzione** | Actionable items for the week — what happened, why it matters *for you*, what to do |
| **Per area tematica** | Deep analysis by category — 3-4 sentence paragraphs connecting news to broader trends |
| **Da leggere con calma** | Long reads worth your time, with a reason *why* for each |
| **Spunti** | 3-5 concrete ideas for posts, reflections, or actions inspired by the day's news |

### Output Formats

Choose your preferred format in Settings — each is professionally typeset, not a raw text dump:

| Format | Details |
|--------|---------|
| **DOCX** | Calibri typography, branded headers with diamond accent, section headers with colored left border, clickable hyperlinks, page numbers. Opens in Word, Pages, or Preview. |
| **PDF** | A4 with 2.5cm margins, print-ready layout via WeasyPrint. Same editorial styling as the HTML version. |
| **EPUB** | Reflowable e-book with embedded CSS. Opens in Apple Books or any EPUB reader. |
| **HTML** | Always generated alongside your chosen format. Standalone page with editorial styling (Georgia serif, max-width 680px, accent borders). |

### HTML Portal

Every time a briefing is generated, Specola also produces a static `index.html` in your output directory — a browsable archive of all your briefings:

- Today's briefing highlighted with an accent border
- Each card shows date, first 3 highlights, and feed/item count
- Click any card to open the full standalone HTML briefing
- Pure HTML + CSS, no JavaScript required — works as a local `file://` page

### Notification Center Widget

A native macOS widget (medium or large) shows today's highlights at a glance:

- "Da sapere oggi" bullet points from the latest briefing
- Unread count badge
- Tap to open the full briefing in your default app
- Updates automatically after each generation — no polling

### Document Styling

All formats share the Specola design language:

- **Hero title** with accent underline in the Specola brand red
- **Section headers** with colored left border accents
- **Clickable hyperlinks** to every source article
- **Branded header** with "SPECOLA" branding and date
- **Clean typography** — refined spacing, clear visual hierarchy
- **Bold emphasis** for key terms and news titles

Available in **Italian** and **English**.

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **macOS** | 14 (Sonoma) or later |
| **LLM provider** | At least one of: **Claude Code CLI** ([install](https://docs.anthropic.com/en/docs/claude-code)), **OpenAI API key**, or **LM Studio** ([download](https://lmstudio.ai)) running locally |
| **Python** | 3.9+ (ships with macOS, or install via `brew install python`) |
| **RSS feeds** | An OPML file exported from any feed reader (Feedly, NetNewsWire, Inoreader, etc.) |

---

## Installation

### From source (recommended)

```bash
# Clone
git clone https://github.com/amargiovanni/specola.git
cd specola

# Build the Release app
xcodebuild -project Specola.xcodeproj -scheme Specola \
    -configuration Release -derivedDataPath build

# Copy to Applications
cp -R build/Build/Products/Release/Specola.app /Applications/
```

The Python engine is **bundled inside the app**. On first launch, Specola automatically copies it to `~/Library/Application Support/Specola/engine/` and creates a virtual environment with all dependencies. No manual Python setup required.

### Prerequisites

If you need to regenerate the Xcode project (e.g., after modifying `project.yml`):

```bash
brew install xcodegen
xcodegen generate
```

---

## Quick Start

1. **Launch Specola** from Applications — a binoculars icon appears in your menubar
2. **Click the icon** to open the popover
3. **Click "Impostazioni..."** to open the Settings window
4. **Fonti tab** — click "Scegli file OPML..." and import your feeds
5. **Profilo tab** — describe your role, stack, interests, and projects in plain text. The more detail you provide, the better Specola personalizes the briefing
7. **Avanzate tab** (optional) — pick your LLM provider: Claude CLI (default), OpenAI (enter API key), or LM Studio (start server first)
8. **Close Settings** and click **"Genera ora"** in the popover
9. Wait a few minutes — Specola fetches all feeds, sends the digest to your AI for analysis, and renders the output
10. A macOS notification appears when done. The briefing opens with a click.

From tomorrow, the briefing generates automatically at your configured time. If your Mac is asleep, it runs as soon as it wakes up.

### Profile Tips

The profile is free-form text. The richer it is, the more relevant the briefing. Example:

> Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS Lambda, PostgreSQL. Mi interessa: regolamentazione EU (AI Act, PSD3, DORA), sicurezza API, trend VC europeo, open source. Sto valutando la migrazione a Bun. Progetti attivi: piattaforma di pagamenti B2B, integrazione con PagoPA.

---

## Architecture

Specola is a three-component system. The Swift app handles UI and scheduling; the Python engine does the heavy lifting; a WidgetKit extension surfaces highlights in Notification Center. They communicate via JSON over stdout and App Groups.

```
┌──────────────────────────────────────────────────────────────────┐
│                         macOS (.app)                              │
│                                                                   │
│  ┌──────────────────┐         ┌───────────────────────────────┐  │
│  │  Swift App (UI)  │         │      Python Engine (CLI)      │  │
│  │                  │  args   │                               │  │
│  │  MenuBarExtra    │────────▶│  1. Parse OPML                │  │
│  │  Popover         │         │  2. Fetch RSS (20 threads)    │  │
│  │  Settings        │  JSON   │  3. Build prompt + profile    │  │
│  │  Scheduler       │◀────────│  4. Analyze (Claude/OpenAI/   │  │
│  │  Notifications   │  stdout │     LMStudio)                 │  │
│  │                  │         │  5. Render HTML (always)      │  │
│  └────────┬─────────┘         │  6. Render DOCX/PDF/EPUB      │  │
│           │                   │  7. Regenerate portal index    │  │
│    App Group                  │  8. Extract highlights         │  │
│           │                   └───────────────────────────────┘  │
│  ┌────────▼─────────┐                                            │
│  │  Widget Extension │                                           │
│  │  WidgetKit        │  Reads widget_data.json from              │
│  │  systemMed/Large  │  App Group shared container               │
│  └──────────────────┘                                            │
│                                                                   │
│  Application Support/Specola/                                     │
│  ├── engine/.venv/    (auto-created on first launch)              │
│  ├── Feeds.opml       (copy of user's OPML)                      │
│  ├── profile.md       (user's professional profile)               │
│  └── history.json     (last 30 briefings metadata)                │
│                                                                   │
│  ~/Documents/Specola/                                             │
│  ├── index.html       (browsable portal archive)                  │
│  ├── Specola_*.html   (standalone briefings)                      │
│  └── Specola_*.docx   (or .pdf or .epub)                         │
└──────────────────────────────────────────────────────────────────┘
```

### Why Two Languages?

| Concern | Best tool | Why |
|---------|-----------|-----|
| RSS parsing | Python (`feedparser`) | Mature, handles every RSS/Atom edge case |
| Concurrent fetching | Python (`ThreadPoolExecutor`) | Simple, effective for I/O-bound work |
| DOCX generation | Python (`python-docx`) | Only viable library for styled DOCX |
| PDF generation | Python (`weasyprint`) | HTML→PDF with full CSS support |
| EPUB generation | Python (`ebooklib`) | Standard EPUB3 output |
| HTML portal | Python (string templates) | Static HTML, zero dependencies |
| LLM invocation | Python (`subprocess` / `urllib`) | Claude via CLI subprocess, OpenAI/LMStudio via HTTP API — zero external dependencies |
| macOS menubar UI | Swift (SwiftUI `MenuBarExtra`) | Native, lightweight, no dock icon |
| Notification Center widget | Swift (WidgetKit) | Native widget with App Group data sharing |
| Scheduling & wake detection | Swift (`Timer` + `NSWorkspace`) | Proper OS integration |
| Notifications | Swift (`UNUserNotificationCenter`) | Native macOS notifications |
| App lifecycle | Swift | Login items, sandboxing, bundle management |

### Interface Contract

```
Swift → Python:  Process() with CLI arguments
                 --opml, --profile, --output-dir, --hours, --language, --format
                 --provider claude|openai|lmstudio
                 --api-key (OpenAI), --endpoint (LMStudio/OpenAI), --model

Python → Swift:  JSON on stdout
                 {"status": "ok", "output_path": "...", "html_path": "...",
                  "portal_path": "...", "feed_count": N, "item_count": N,
                  "highlights": ["...", "..."]}
                 {"status": "error", "message": "..."}
```

### Python Engine Modules

| Module | Responsibility | Key details |
|--------|---------------|-------------|
| `feed_fetcher.py` | OPML parsing + RSS fetch | `xml.etree.ElementTree` for OPML, `feedparser` for RSS, `ThreadPoolExecutor` with 20 workers, strips HTML, filters by time window, handles timezone-aware dates |
| `prompt_builder.py` | Prompt assembly | Three-part prompt: system instruction + user profile (verbatim) + output instructions. Hardcoded IT/EN templates. Appends category list. |
| `analyzer.py` | LLM invocation | Routes to Claude CLI (`subprocess`), OpenAI API (`urllib`), or LMStudio (`urllib`). No retry, no backoff. Configurable timeout. Returns None on failure. Zero external HTTP dependencies. |
| `doc_generator.py` | DOCX rendering | Line-by-line markdown parsing with regex. Heading styles, bold runs, hyperlinks, horizontal rules. A4/Calibri/1.3 line height. Branded header/footer. Fallback mode for when Claude is unavailable. |
| `html_generator.py` | HTML rendering | Shared `markdown_to_html()` function + standalone HTML page with inline CSS. Editorial styling (Georgia serif, 680px max-width, accent borders). Used by PDF and EPUB generators. |
| `pdf_generator.py` | PDF rendering | Takes HTML from `html_generator` and converts to PDF via WeasyPrint. A4, 2.5cm margins, `@media print` rules. |
| `epub_generator.py` | EPUB rendering | Creates EPUB3 from markdown via ebooklib. Single chapter, embedded CSS, language-aware metadata. |
| `portal_generator.py` | Portal index + highlights | Scans output directory for HTML briefings, generates `index.html` with card previews. Also provides `extract_highlights()` for widget data. |

### Swift App Components

| File | Role |
|------|------|
| `SpecolaApp.swift` | `@main` entry, `MenuBarExtra` with dynamic badge icon, `Settings` scene, first-launch flow, engine setup, `specola://` URL scheme handler |
| `MenuBarView.swift` | Popover: header with last generation time, scrollable history list (10 items), "Genera ora" with progress state, settings/quit footer |
| `SettingsView.swift` | `TabView` with 4 tabs: Fonti (OPML picker), Pianificazione (time picker, auto-generate, login item), Profilo (multiline text editor), Avanzate (LLM provider picker with conditional config, format picker, output dir, language, time window) |
| `Models/AppState.swift` | `@Observable` class: history array, generation state, unread count, JSON persistence, max 30 entries, widget data updates via App Group |
| `Models/Settings.swift` | `SpecolaSettings` enum wrapping `UserDefaults` + computed paths for Application Support |
| `Models/SpecolaEntry.swift` | `Codable` struct: id, date, path, htmlPath, feedCount, itemCount, highlights, read (backwards-compatible decoding) |
| `Models/WidgetData.swift` | Shared `Codable` model for widget data: date, highlights, unread count, latest path |
| `Services/EngineService.swift` | Async `Process()` launch with provider-specific args (--provider, --api-key, --endpoint), stdout JSON parsing, typed errors |
| `Services/SchedulerService.swift` | 60-second `Timer` + `NSWorkspace.didWakeNotification`. Pure `shouldGenerate()` function for testability |
| `Services/NotificationService.swift` | `UNUserNotificationCenter` — permission request, success/error notifications |
| `Helpers/MenuBarIcon.swift` | Renders `binoculars` SF Symbol + red badge overlay as `NSImage` |
| `SpecolaWidget/` | WidgetKit extension: `TimelineProvider` reading from App Group, `systemMedium`/`systemLarge` views with highlights and unread badge |

---

## Configuration

### Settings Window

| Tab | Controls |
|-----|----------|
| **Fonti** | OPML file picker (`.opml`, `.xml`), feed count summary, remove button. File is copied to Application Support. |
| **Pianificazione** | Hour/minute picker (default: 07:00), "Genera automaticamente" toggle, "Avvia al login" toggle (via `SMAppService`) |
| **Profilo** | Multiline text editor (min 200pt height). Auto-saves on focus loss. No character limit. |
| **Avanzate** | LLM provider picker (Claude/OpenAI/LM Studio) with conditional config per provider, output format picker (DOCX/PDF/EPUB), output directory, language picker (IT/EN), time window stepper (6-72h) |

### Data Storage

| Data | Location | Format |
|------|----------|--------|
| App settings | `UserDefaults` (com.oltrematica.specola) | Key-value (incl. LLM provider, API keys, endpoints) |
| User profile | `~/Library/Application Support/Specola/profile.md` | Plain text |
| OPML feeds | `~/Library/Application Support/Specola/Feeds.opml` | XML |
| Briefing history | `~/Library/Application Support/Specola/history.json` | JSON array (max 30 entries) |
| Python engine | `~/Library/Application Support/Specola/engine/` | Python venv + source |
| Generated briefings | `~/Documents/Specola/Specola_YYYY-MM-DD.*` | DOCX, PDF, EPUB, or HTML |
| Portal index | `~/Documents/Specola/index.html` | Static HTML |
| Widget data | App Group shared container `/widget_data.json` | JSON |

---

## Engine CLI Reference

The Python engine can be used standalone, independent of the Swift app:

```bash
cd engine

# With Claude CLI (default)
.venv/bin/python specola_engine.py run \
    --opml ~/feeds.opml \
    --profile ~/profile.md \
    --output-dir ~/Documents/Specola \
    --language it --hours 24

# With OpenAI
.venv/bin/python specola_engine.py run \
    --opml ~/feeds.opml \
    --profile ~/profile.md \
    --output-dir ~/Documents/Specola \
    --provider openai --api-key sk-... --model gpt-4o

# With LM Studio (local)
.venv/bin/python specola_engine.py run \
    --opml ~/feeds.opml \
    --profile ~/profile.md \
    --output-dir ~/Documents/Specola \
    --provider lmstudio --model llama-3.3-70b
```

### All Options

```
specola_engine.py run [options]

Required:
  --opml PATH           OPML file with RSS feed URLs
  --profile PATH        Plain text file describing the user's professional profile
  --output-dir PATH     Directory where output files are saved

LLM Provider:
  --provider PROVIDER   LLM backend: claude, openai, lmstudio (default: claude)
  --api-key KEY         API key (required for openai provider)
  --endpoint URL        Custom API endpoint (openai or lmstudio; defaults to
                        api.openai.com or localhost:1234 respectively)
  --model MODEL         Model name (provider-specific, e.g. gpt-4o, llama-3.3-70b)

Optional:
  --format FMT          Output format: docx, pdf, epub (default: docx). HTML is always generated.
  --hours N             Only include articles from the last N hours (default: 24)
  --language it|en      Briefing language (default: it)
  --max-items N         Maximum items per feed category (default: 30)
  --dry-run             Fetch feeds and report counts, but skip analysis and rendering
  --verbose             Enable DEBUG logging to stderr
```

### Output Format

Stdout (always JSON):

```json
// Success
{"status": "ok", "output_path": "/path/to/Specola_2026-04-05.pdf",
 "html_path": "/path/to/Specola_2026-04-05.html",
 "portal_path": "/path/to/index.html",
 "feed_count": 187, "item_count": 42,
 "highlights": ["EU AI Act enters enforcement...", "GitHub Copilot Workspace GA..."]}

// Dry run
{"status": "ok", "feed_count": 187, "item_count": 42}

// Error
{"status": "error", "message": "Nessun feed trovato nel file OPML"}
```

Stderr: logging (WARNING by default, DEBUG with `--verbose`).

### Fallback Behavior

If Claude CLI fails (not found, timeout, error), the engine **still generates output** from the raw feed digest with a warning banner: "Analisi non disponibile." The HTML version is always produced; the chosen format falls back gracefully. This ensures you always get *something*, even if the AI analysis is temporarily unavailable.

---

## Development

### Running Tests

```bash
# Python engine — 353 tests
cd engine
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v

# Swift app — 80+ tests
xcodebuild test -project Specola.xcodeproj -scheme Specola \
    -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO
```

### Build from Source

```bash
# Regenerate Xcode project (after modifying project.yml or adding files)
xcodegen generate

# Debug build
xcodebuild -project Specola.xcodeproj -scheme Specola build

# Release build → /Applications
xcodebuild -project Specola.xcodeproj -scheme Specola \
    -configuration Release -derivedDataPath build
cp -R build/Build/Products/Release/Specola.app /Applications/
```

### Regenerating the App Icon

The app icon is generated programmatically from the `binoculars.fill` SF Symbol:

```bash
swift scripts/generate_icon.swift Specola/Assets.xcassets/AppIcon.appiconset
```

This renders the icon at all 10 required macOS sizes (16px to 1024px) with the Specola brand colors: navy gradient background, white binoculars, red accent bar.

### Project Structure

```
specola/
├── Specola/                        # Swift app source
│   ├── SpecolaApp.swift            # @main, MenuBarExtra, first launch
│   ├── MenuBarView.swift           # Popover UI
│   ├── SettingsView.swift          # Four-tab settings (TabView)
│   ├── Models/
│   │   ├── SpecolaEntry.swift      # History entry (Codable)
│   │   ├── AppState.swift          # @Observable app state
│   │   └── Settings.swift          # UserDefaults wrapper
│   ├── Services/
│   │   ├── EngineService.swift     # Python engine launcher
│   │   ├── SchedulerService.swift  # Timer + wake detection
│   │   └── NotificationService.swift
│   ├── Helpers/
│   │   └── MenuBarIcon.swift       # Badge icon renderer
│   └── Assets.xcassets/
│       └── AppIcon.appiconset/     # Generated icon (10 sizes)
├── SpecolaTests/                   # Swift unit tests (80+)
│   ├── SpecolaEntryTests.swift     # JSON encode/decode, backward compat
│   ├── AppStateTests.swift         # History, unread count, max entries
│   ├── EngineServiceTests.swift    # JSON output parsing, error descriptions
│   ├── SchedulerServiceTests.swift # Scheduling logic, minute-level edges
│   ├── SettingsTests.swift         # All defaults, set/get, provider config
│   └── WidgetDataTests.swift       # Encode/decode, placeholder, unicode
├── engine/                         # Python engine (bundled in .app)
│   ├── specola_engine.py           # CLI entry point + orchestration
│   ├── requirements.txt            # feedparser, python-docx, python-dateutil, weasyprint, ebooklib
│   ├── requirements-dev.txt        # + pytest
│   ├── setup_engine.sh             # venv creation script
│   ├── src/
│   │   ├── feed_fetcher.py         # OPML + RSS + digest
│   │   ├── prompt_builder.py       # IT/EN prompt templates
│   │   ├── analyzer.py             # LLM invocation (Claude CLI / OpenAI / LMStudio)
│   │   ├── doc_generator.py        # DOCX renderer
│   │   ├── html_generator.py       # Markdown → HTML (shared conversion + standalone page)
│   │   ├── pdf_generator.py        # HTML → PDF via WeasyPrint
│   │   ├── epub_generator.py       # Markdown → EPUB via ebooklib
│   │   └── portal_generator.py     # Portal index + highlight extraction
│   └── tests/                      # pytest tests
├── SpecolaWidget/                  # Notification Center widget extension
│   ├── SpecolaWidget.swift         # Widget bundle + TimelineProvider
│   ├── SpecolaWidgetEntry.swift    # Timeline entry model
│   └── SpecolaWidgetView.swift     # SwiftUI views (systemMedium/Large)
├── scripts/
│   └── generate_icon.swift         # App icon generator
├── project.yml                     # xcodegen project definition
├── CLAUDE.md                       # AI assistant instructions
├── LICENSE                         # MIT
└── README.md
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Multi-provider LLM** | Choose Claude CLI (zero-config), OpenAI API (cloud), or LM Studio (fully offline). Provider abstraction uses stdlib `urllib` — zero new dependencies for HTTP providers. |
| **Native Swift, not Electron** | A menubar app should be invisible when you don't need it. ~15 MB, not ~200 MB. |
| **Python for the engine** | `feedparser` handles every RSS/Atom edge case. `python-docx` is the only viable DOCX library. Both are battle-tested. |
| **Two processes, not one** | Clean separation. The engine is testable standalone. The app is pure UI. Neither depends on the other's internals. |
| **Multi-format with HTML always-on** | DOCX for editability, PDF for sharing, EPUB for reading. HTML is always generated because it feeds the portal archive and is the lightest, most portable format. |
| **No async Python** | `ThreadPoolExecutor` is simpler and perfectly adequate for I/O-bound RSS fetching. No event loop complexity. |
| **No Core Data** | 30 JSON entries don't need a database. `Codable` + file I/O is simpler and more debuggable. |
| **No launchd** | An internal timer + wake-from-sleep observer keeps scheduling self-contained. No system-level configuration to manage. |
| **Bundled engine** | The Python engine ships inside the `.app` bundle. On first launch it's copied to Application Support and the venv is created automatically. Zero manual setup. |
| **Links in every item** | Every cited news item includes a clickable hyperlink to the original source. The briefing is a starting point for deeper reading, not a replacement. |
| **Static portal, not a web server** | `index.html` is a static file, not a running server. No port conflicts, no process management — just a file you open in a browser. |
| **App Group for widget** | WidgetKit extensions run in a separate process. App Groups provide a clean, Apple-sanctioned data sharing mechanism via a shared JSON file. |

---

## Troubleshooting

### "Genera ora" is disabled
You need to import an OPML file first. Open Settings (click the menubar icon, then "Impostazioni..."), go to the "Fonti" tab, and select your OPML file.

### Claude CLI not found
If using Claude provider: Specola looks for `claude` in `/usr/local/bin/`, `~/.local/bin/`, `~/.claude/local/`, and the system PATH. If it's installed elsewhere, set the path in Settings > Avanzate > Claude Code CLI.

### OpenAI API errors
Verify your API key in Settings > Avanzate. Check that the model name is valid (default: `gpt-4o`). API errors are logged to stderr.

### LM Studio not connecting
Make sure LM Studio is running with the local server enabled (default: `http://localhost:1234`). Load a model in LM Studio before generating. If using a custom port, update the endpoint in Settings > Avanzate.

### Engine setup fails on first launch
You can set up the engine manually:
```bash
cd ~/Library/Application\ Support/Specola/engine/
bash setup_engine.sh
```

### Briefing shows "Analisi non disponibile"
The LLM provider failed or timed out. The output still contains the raw feed digest. Check your provider: for Claude, run `echo "test" | claude -p "say hi"`; for OpenAI, verify the API key; for LM Studio, ensure the server is running.

### No notification after generation
Go to System Settings > Notifications > Specola and enable notifications.

---

## License

MIT License. See [LICENSE](LICENSE).

---

*Built with Swift, Python, and [Claude Code](https://claude.ai/claude-code). Supports Claude, OpenAI, and local LLMs via LM Studio.*
