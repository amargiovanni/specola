# Specola — Multi-format output, HTML portal, Notification Center widget

**Date:** 2026-04-06
**Status:** Draft
**Origin:** Feedback from Enrico Ferraris + Andrea Margiovanni

---

## Summary

Three features that extend Specola's output and accessibility:

1. **Multi-format output** — user chooses DOCX, PDF, or EPUB in settings (one at a time). HTML standalone is always generated in addition.
2. **HTML portal** — static `index.html` in the output directory, auto-regenerated at each run, listing all briefings with preview bullets. Each briefing also has its own standalone HTML page.
3. **Notification Center widget** — macOS WidgetKit extension (systemMedium + systemLarge) showing "Da sapere oggi" highlights from the latest briefing.

---

## Feature 1: Multi-format output

### User-facing behavior

- New segmented picker in Settings > Advanced: `DOCX | PDF | EPUB` (default: DOCX)
- Each generation produces **two files**: the chosen format + an HTML standalone
- The HTML standalone is always generated because it feeds the portal index and the widget data extraction

### Python engine changes

#### New CLI argument

```
--format docx|pdf|epub    (default: docx)
```

#### New modules

| Module | Purpose | Dependency |
|--------|---------|------------|
| `engine/src/html_generator.py` | Markdown → HTML standalone with inline CSS | None (string templates) |
| `engine/src/pdf_generator.py` | HTML file → PDF via weasyprint | `weasyprint` |
| `engine/src/epub_generator.py` | Markdown → EPUB via ebooklib | `ebooklib` |

`engine/src/doc_generator.py` remains unchanged (DOCX generation).

#### html_generator.py

Converts the briefing markdown to a self-contained HTML file with inline CSS.

**Style:** Minimale editoriale — `max-width: 680px` centered, Georgia/serif body text, sans-serif UI elements, colors matching the DOCX palette (#1a1a2e headings, #e94560 accent, #16213e subheadings).

**Parsing:** Same regex line-by-line approach as `doc_generator.py`:
- `# ` → `<h1>`
- `## ` → `<h2>` with left accent border
- `### ` → `<h3>`
- `- ` / `* ` → `<li>` in `<ul>`
- `1. ` → `<li>` in `<ol>`
- `**text**` → `<strong>`
- `[text](url)` → `<a href>`
- `---` → `<hr>`
- Empty lines → close current block
- Everything else → `<p>`

**Output:** `Specola_YYYY-MM-DD.html` in the output directory.

**Structure of the HTML file:**
- `<!DOCTYPE html>` full document
- `<meta charset="utf-8">`
- Inline `<style>` block (no external CSS)
- Header: "Specola" + date + feed/item counts
- Body: converted markdown
- Footer: "Generato da Specola" + timestamp

#### pdf_generator.py

Takes the HTML file produced by `html_generator` and converts it to PDF.

```python
from weasyprint import HTML

def generate_pdf(html_path: Path, date: str, output_dir: str) -> str:
    pdf_path = Path(output_dir) / f"Specola_{date}.pdf"
    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    return str(pdf_path)
```

The CSS in the HTML handles print layout: `@media print` rules for A4, 2.5cm margins, page-break controls, header/footer via `@page`.

#### epub_generator.py

Creates an EPUB3 from the briefing markdown.

```python
from ebooklib import epub

def generate_epub(markdown: str, date: str, output_dir: str, language: str) -> str:
    book = epub.EpubBook()
    book.set_identifier(f"specola-{date}")
    book.set_title(f"Specola — Briefing del {date}")
    book.set_language("it" if language == "it" else "en")

    # Single chapter with HTML content (reuse html_generator's conversion logic)
    chapter = epub.EpubHtml(title="Briefing", file_name="briefing.xhtml")
    chapter.content = markdown_to_html_body(markdown)  # shared with html_generator
    chapter.add_link(href="style.css", rel="stylesheet", type="text/css")

    book.add_item(chapter)
    # Add minimal CSS, nav, spine...

    epub_path = Path(output_dir) / f"Specola_{date}.epub"
    epub.write_epub(str(epub_path), book)
    return str(epub_path)
```

#### Shared markdown→HTML conversion

Both `html_generator` and `epub_generator` need markdown→HTML body conversion. Extract a shared function `markdown_to_html(markdown: str) -> str` into `html_generator.py` and import it from `epub_generator.py`. This avoids duplicating the parsing logic.

#### Orchestration in specola_engine.py

```python
# 1. Always generate HTML standalone
html_path = generate_html(markdown, date_str, args.output_dir)

# 2. Generate the chosen format (if not just HTML)
if args.format == "docx":
    main_path = generate_docx(markdown, date_str, args.output_dir)
elif args.format == "pdf":
    main_path = generate_pdf(html_path, date_str, args.output_dir)
elif args.format == "epub":
    main_path = generate_epub(markdown, date_str, args.output_dir, args.language)
else:
    main_path = html_path  # fallback

# 3. Regenerate portal index
regenerate_portal_index(args.output_dir)

# 4. Extract highlights for widget
highlights = extract_highlights(markdown)
```

#### Extract highlights

```python
def extract_highlights(markdown: str) -> list[str]:
    """Extract bullet points from 'Da sapere oggi' / 'Key takeaways' section."""
    # Find the section, collect bullet lines until next ## heading
    # Return list of plain text strings (max 5)
```

Simple regex: find `## Da sapere oggi` (or `## Key takeaways` for EN), collect `- ` or `* ` lines until the next `## ` or end.

#### JSON output (extended)

```json
{
  "status": "ok",
  "output_path": "/path/Specola_2026-04-06.pdf",
  "html_path": "/path/Specola_2026-04-06.html",
  "portal_path": "/path/index.html",
  "feed_count": 187,
  "item_count": 42,
  "highlights": [
    "EU approva regolamento AI Act...",
    "GitHub Copilot Workspace in GA...",
    "Vulnerabilita critica OpenSSL 3.x..."
  ]
}
```

#### New dependencies

Add to `requirements.txt`:
```
weasyprint
ebooklib
```

#### Fallback behavior

If the chosen format fails (e.g., weasyprint not installed), the engine:
1. Logs the error to stderr
2. Falls back to HTML-only (already generated)
3. Returns JSON with `output_path` pointing to the HTML file and a `warning` field explaining the fallback

### Swift app changes

#### SpecolaSettings

New key:
```swift
static var outputFormat: String  // "docx" | "pdf" | "epub", default "docx"
```

#### SettingsView > AdvancedTab

New segmented Picker above the language picker:
```swift
Picker("Formato di output", selection: $outputFormat) {
    Text("DOCX").tag("docx")
    Text("PDF").tag("pdf")
    Text("EPUB").tag("epub")
}
.pickerStyle(.segmented)
```

#### EngineService

Pass `--format` to the Python process:
```swift
process.arguments += ["--format", SpecolaSettings.outputFormat]
```

Parse new JSON fields: `html_path`, `portal_path`, `highlights`.

#### EngineResult (extended)

```swift
struct EngineResult {
    let outputPath: String?
    let htmlPath: String?
    let portalPath: String?
    let feedCount: Int
    let itemCount: Int
    let highlights: [String]
}
```

#### SpecolaEntry (extended)

```swift
struct SpecolaEntry: Codable, Identifiable {
    let id: String
    let date: Date
    let path: String
    let htmlPath: String
    let feedCount: Int
    let itemCount: Int
    let highlights: [String]
    var read: Bool
}
```

Backwards compatibility: custom `Decodable` init with defaults for `htmlPath` (`""`) and `highlights` (`[]`) so old history.json entries still parse.

#### MenuBarView

No changes. Tap still opens `entry.path` — the OS opens the correct app based on file extension (.pdf → Preview, .epub → Books, .docx → Word).

---

## Feature 2: HTML Portal

### User-facing behavior

- A static `index.html` in the output directory (e.g., `~/Documents/Specola/index.html`)
- Regenerated automatically every time a new Specola is generated
- Lists all briefings that have a corresponding `.html` file in the directory
- Sorted by date descending, newest first
- Each card shows: date, title, first 3 highlight bullets, feed/item count, format badge
- Today's card highlighted with accent border and "Oggi" / "Today" label
- Click on a card title opens the standalone HTML briefing in the browser
- No JavaScript required for navigation (pure HTML + CSS, file:// friendly)

### portal_generator.py

```python
def regenerate_portal_index(output_dir: str, language: str = "it") -> str:
    """Scan output_dir for Specola_*.html files, generate index.html."""

    # 1. Glob Specola_YYYY-MM-DD*.html files (exclude index.html)
    # 2. For each file: extract date from filename, parse first 3 bullet points
    #    from the HTML (regex on <li> or <strong> tags in the first section)
    # 3. Sort by date descending
    # 4. Generate index.html with inline CSS

    # Returns path to index.html
```

### Visual design

**Layout:** Single column, `max-width: 680px` centered, `font-family: Georgia, serif`.

**Header:** "Specola" bold 32px + "Archivio briefing · N numeri" subtitle.

**Cards:**
- Date label: uppercase, letterspaced, 11px, sans-serif
- Title: 18px bold, links to the standalone HTML
- Preview: first 3 bullets from the briefing, 14px, muted color
- Meta: "N fonti · M articoli · FORMAT" in 12px gray
- Today's card: left border 3px #e94560, "Oggi" label in accent color
- Older cards: no left border, separated by 1px bottom border

**Footer:** "Generato da Specola · Aggiornato il [data]" centered, 12px gray.

### Integration

The portal index is generated by the Python engine as the last step. The Swift app receives `portal_path` in the JSON result but does not need to act on it — the index lives in the user's output directory and is opened manually in the browser.

Optional future enhancement: add "Apri portale" button in the MenuBarView popover footer. Not in scope for this iteration.

---

## Feature 3: Notification Center Widget

### Architecture

A WidgetKit extension — a separate Xcode target that runs in its own process. Communicates with the main app via an App Group shared container.

### Xcode setup

- New target: `SpecolaWidget` (Widget Extension)
- Deployment target: macOS 14 (Sonoma)
- App Group: `group.com.oltrematica.specola` (or matching the existing bundle ID pattern)
- Both the main app and the widget extension need the App Group entitlement

### File structure

```
Specola/
├── SpecolaWidget/
│   ├── SpecolaWidget.swift           # @main WidgetBundle, widget definition
│   ├── SpecolaWidgetEntry.swift      # TimelineEntry model
│   ├── SpecolaWidgetView.swift       # SwiftUI views for each size family
│   └── Info.plist
```

### Shared data

The main app writes a JSON file to the App Group container after each generation and after each `markAsRead()`:

**Path:** `<AppGroupContainer>/widget_data.json`

```json
{
  "date": "2026-04-06T07:00:00Z",
  "dateLabel": "6 aprile 2026",
  "unreadCount": 2,
  "highlights": [
    "EU approva regolamento AI Act: impatti immediati per sistemi ad alto rischio",
    "GitHub Copilot Workspace disponibile in GA per tutti i piani",
    "Vulnerabilita critica OpenSSL 3.x — patch urgente disponibile",
    "Redis 8.0 cambia licenza: triple license RSALv2/SSPLv1/AGPLv3",
    "Apple WWDC 2026 date confermate: 8-12 giugno"
  ],
  "latestPath": "/Users/andrea/Documents/Specola/Specola_2026-04-06.pdf"
}
```

### Writing widget data (main app)

In `AppState`, new method called after generation success and after `markAsRead()`:

```swift
func updateWidgetData() {
    guard let latest = history.first else { return }
    let data = WidgetData(
        date: latest.date,
        dateLabel: latest.date.formatted(...),
        unreadCount: unreadCount,
        highlights: latest.highlights,
        latestPath: latest.path
    )
    let url = FileManager.default
        .containerURL(forSecurityApplicationGroupIdentifier: appGroupID)!
        .appendingPathComponent("widget_data.json")
    try? JSONEncoder().encode(data).write(to: url)
    WidgetCenter.shared.reloadAllTimelines()
}
```

### TimelineProvider

```swift
struct Provider: TimelineProvider {
    func placeholder(in context: Context) -> WidgetEntry {
        WidgetEntry(date: .now, data: .placeholder)
    }

    func getSnapshot(in context: Context, completion: @escaping (WidgetEntry) -> Void) {
        completion(WidgetEntry(date: .now, data: loadWidgetData() ?? .placeholder))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<WidgetEntry>) -> Void) {
        let data = loadWidgetData() ?? .placeholder
        let entry = WidgetEntry(date: .now, data: data)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
    }
}
```

Timeline policy is `.never` — the widget only updates when the app explicitly calls `WidgetCenter.shared.reloadAllTimelines()`. No polling.

### Widget sizes

#### systemLarge

```
┌─────────────────────────────┐
│  Specola                    │
│  6 aprile 2026 · 2 non lette│
│─────────────────────────────│
│  Da sapere oggi             │
│                             │
│  • EU approva regolamento   │
│    AI Act: impatti su...    │
│                             │
│  • GitHub Copilot workspace │
│    disponibile in GA        │
│                             │
│  • Vulnerabilita critica    │
│    in OpenSSL 3.x...        │
│                             │
│  • Redis 8.0 cambia licenza │
│    tri-license RSALv2/SSPL  │
│                             │
│  • Apple WWDC 2026 date     │
│    confermate: 8-12 giugno  │
│                             │
│         [ Apri briefing ]   │
└─────────────────────────────┘
```

- Header: "Specola" bold + date + unread badge
- Section title: "Da sapere oggi" in accent color
- Up to 5 bullet points from `highlights`
- Footer area: tappable, opens latest briefing

#### systemMedium (fallback)

Same layout, truncated: header + first 3 bullets, no explicit button (entire widget is tappable).

### Deep link

```swift
.widgetURL(URL(string: "specola://open-latest"))
```

The main app handles this URL scheme in `SpecolaApp.swift`:

```swift
.onOpenURL { url in
    if url.scheme == "specola", url.host == "open-latest" {
        if let latest = appState.history.first {
            NSWorkspace.shared.open(URL(fileURLWithPath: latest.path))
            appState.markAsRead(id: latest.id)
        }
    }
}
```

### Empty state

If no briefing has been generated yet, the widget shows:
- "Specola" header
- "Nessun briefing disponibile" centered
- "Configura l'app per iniziare" subtitle

### Widget configuration

No configuration intent needed for v1. The widget always shows the latest briefing. Future enhancement: let user pick which section to show (not in scope).

---

## Dependencies summary

### New Python packages

| Package | Version | Purpose |
|---------|---------|---------|
| `weasyprint` | latest | HTML → PDF conversion |
| `ebooklib` | latest | EPUB generation |

### New Xcode target

| Target | Type | Entitlements |
|--------|------|-------------|
| `SpecolaWidget` | Widget Extension | App Group |

### Entitlement changes

Both main app and widget extension need:
```xml
<key>com.apple.security.application-groups</key>
<array>
    <string>group.com.oltrematica.specola</string>
</array>
```

---

## Out of scope

- Multiple formats per run (only one chosen format + HTML)
- Web server for the portal (static files only)
- Widget configuration intent (always shows latest)
- "Apri portale" button in menubar popover (future enhancement)
- Dark mode for HTML portal and widget (future enhancement)
- Sharing/export features
- Automatic cleanup of old HTML files
