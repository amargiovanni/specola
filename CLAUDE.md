# CLAUDE.md — Specola

## Cosa è Specola

App nativa macOS con icona nel menubar che ogni giorno, all'orario configurato dall'utente, raccoglie le novità dalle fonti RSS di un file OPML, le fa analizzare dalla CLI di Claude Code in base al profilo professionale dell'utente, e produce un briefing approfondito in formato DOCX (una "Specola").

Il nome viene dalla specola: l'osservatorio da cui si scruta l'orizzonte.

Specola non è legata a nessun contesto professionale specifico. L'utente configura il proprio profilo (ruolo, stack, interessi, progetti) e Specola usa quel profilo per filtrare, prioritizzare e contestualizzare le notizie.

## Architettura a due livelli

Specola è composta da due parti:

### 1. App Swift (UI + orchestrazione)

App macOS nativa in Swift/SwiftUI. Vive nel menubar. Gestisce:
- Icona menubar con badge contatore (Specole non lette)
- Popover/dropdown con lista ultime Specole
- Settings: OPML, orario, profilo utente
- Scheduling: timer interno + gestione wake-from-sleep
- Lancio del motore Python e tracking dello stato

### 2. Motore Python (engine)

Script Python che fa il lavoro pesante:
- Parsing OPML e fetch concorrente dei feed RSS
- Costruzione del digest markdown
- Invocazione della CLI di Claude Code via subprocess
- Generazione del DOCX finale

L'app Swift invoca il motore Python via `Process()`. Il motore Python è bundled nella cartella dell'app o installato separatamente nella directory di supporto.

Questa separazione esiste perché:
- RSS parsing concorrente con feedparser è maturo e affidabile
- python-docx è l'unica libreria praticabile per generare DOCX di qualità
- La CLI di Claude Code si invoca comodamente da Python via subprocess
- Swift eccelle per l'UI nativa macOS e la gestione del ciclo di vita dell'app

---

## App Swift — Dettagli

### Tecnologie

- Swift 5.9+, SwiftUI
- Target: macOS 14 (Sonoma)+
- Xcode project, no SPM package esterno se non strettamente necessario
- App sandbox: disabilitata (deve invocare processi esterni: python, claude)
- LSUIElement = true (app senza dock icon, solo menubar)
- Login item: opzione nei settings per lancio automatico al login

### Icona Menubar

- Icona: simbolo SF Symbols `binoculars` o `eye` (valutare quale rende meglio a 18×18pt)
- Badge: contatore numerico sovrapposto in alto a destra (stile Mail.app)
- Il contatore mostra il numero di Specole non ancora aperte dall'utente
- Se il contatore è 0, non mostrare il badge
- Click sull'icona: apre il popover

### Popover (click sull'icona)

Il popover contiene, dall'alto in basso:

#### Header
- Titolo "Specola" in grassetto
- Sottotitolo con data/ora dell'ultima generazione

#### Lista Specole
- Ultime 10 Specole generate, ordinate per data decrescente
- Ogni riga mostra:
  - Data (es. "5 aprile 2026")
  - Numero di fonti analizzate
  - Indicatore non letto (pallino blu, come Mail.app)
- Click su una riga: apre il DOCX corrispondente con `NSWorkspace.shared.open()`
- Aprire una Specola la segna come letta (il contatore si decrementa)

#### Azioni
- Pulsante "Genera ora" — lancia il motore immediatamente, indipendentemente dallo scheduling
- Durante la generazione: il pulsante diventa una progress bar indeterminata con "Generazione in corso..."
- Il pulsante è disabilitato durante la generazione

#### Footer
- "Impostazioni..." — apre la finestra Settings
- "Esci" — chiude l'app

### Finestra Settings

Finestra separata (non nel popover), stile macOS standard. Tab o sezioni:

#### Sezione "Fonti"
- Label: path del file OPML attualmente configurato (o "Nessun file OPML configurato")
- Pulsante "Scegli file OPML..." — apre NSOpenPanel, filtro .opml e .xml
- Pulsante "Rimuovi" — rimuove il riferimento al file OPML (disabilita la generazione)
- Dopo aver scelto un file: mostrare un riepilogo (N categorie, M feed totali) parsando l'OPML
- Il file OPML viene copiato nella directory di supporto dell'app (`Application Support/Specola/`) così non dipende dalla posizione originale. Se l'utente lo sostituisce, il vecchio viene sovrascritto.

#### Sezione "Pianificazione"
- Orario di generazione: picker ore/minuti (default: 07:00)
- Checkbox "Genera automaticamente" (default: attiva)
- Nota: "Se il Mac è in stop all'orario previsto, la Specola verrà generata al risveglio."
- Checkbox "Avvia Specola al login" (gestisce il Login Item)

#### Sezione "Profilo"
- Label: "Descrivi il tuo ruolo professionale, il tuo stack, i tuoi interessi e progetti. Specola usa questo profilo per personalizzare l'analisi delle notizie."
- TextEditor multilinea, altezza minima 200pt, ridimensionabile
- Placeholder: "Es: Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS. Mi interessa: regolamentazione EU, sicurezza API, trend VC europeo..."
- Nessun limite di caratteri. Il testo viene salvato così com'è.
- Pulsante "Salva" (o salvataggio automatico on blur)

#### Sezione "Avanzate"
- Directory di output per i DOCX (default: `~/Documents/Specola/`)
- Pulsante "Apri cartella" — `NSWorkspace.shared.open()` sulla directory
- Lingua del briefing: segmented control "Italiano" / "English" (default: Italiano)
- Finestra temporale: stepper "Ultime N ore" (default: 24, min: 6, max: 72)
- Path del binario Claude Code CLI (auto-detected, con possibilità di override manuale)

### Persistenza dati

- Usare `UserDefaults` per le impostazioni semplici (orario, lingua, ore, path)
- Il profilo utente (testo lungo) va salvato come file: `Application Support/Specola/profile.md`
- L'OPML va copiato in: `Application Support/Specola/Feeds.opml`
- La lista delle Specole generate (data, path file, letto/non letto) va salvata come JSON in: `Application Support/Specola/history.json`
- Struttura `history.json`:

```json
[
  {
    "id": "2026-04-05",
    "date": "2026-04-05T07:00:00Z",
    "path": "/Users/andrea/Documents/Specola/Specola_2026-04-05.docx",
    "feedCount": 187,
    "itemCount": 42,
    "read": false
  }
]
```

- Mantenere solo le ultime 30 entry. Alla 31esima, rimuovere la più vecchia (ma non cancellare il file DOCX).

### Scheduling

Non usare launchd. Gestire lo scheduling internamente all'app:

- Timer che controlla ogni 60 secondi se è il momento di generare
- Condizione di generazione: ora corrente >= ora configurata E non è già stata generata una Specola oggi (controllare `history.json`)
- Al wake-from-sleep (`NSWorkspace.didWakeNotification`): controllare immediatamente se la Specola di oggi è stata generata. Se no, e se l'orario è passato, lanciare la generazione.
- La generazione gira in un Task async in background. Non blocca l'UI.
- Durante la generazione: aggiornare l'icona menubar (opzionale: animazione o indicatore)
- Al termine: aggiungere entry in `history.json`, aggiornare il contatore badge, mostrare una notifica macOS nativa (`UNUserNotificationCenter`): "Specola del [data] pronta — N articoli analizzati"

### Invocazione del motore Python

L'app Swift lancia il motore Python così:

```swift
let process = Process()
process.executableURL = URL(fileURLWithPath: pythonPath) // .venv/bin/python
process.arguments = [enginePath, "run",
    "--opml", opmlPath,
    "--profile", profilePath,
    "--output-dir", outputDir,
    "--hours", String(hours),
    "--language", language
]
process.currentDirectoryURL = engineDir

let outputPipe = Pipe()
let errorPipe = Pipe()
process.standardOutput = outputPipe
process.standardError = errorPipe
```

Il motore Python scrive su stdout un JSON alla fine:

```json
{
  "status": "ok",
  "output_path": "/Users/.../Specola_2026-04-05.docx",
  "feed_count": 187,
  "item_count": 42
}
```

Oppure in caso di errore:

```json
{
  "status": "error",
  "message": "Claude CLI non trovata"
}
```

L'app Swift parsa questo JSON per aggiornare lo stato.

### Primo avvio

Al primo avvio (nessun file in Application Support/Specola/):
1. Mostrare la finestra Settings automaticamente
2. Evidenziare che servono almeno: un file OPML e un profilo
3. Il pulsante "Genera ora" nel popover è disabilitato finché non c'è un OPML configurato

### Notifiche

- Usare `UNUserNotificationCenter` per notifiche native macOS
- Al termine della generazione: "Specola del [data] pronta" con action "Apri" che apre il DOCX
- In caso di errore: "Specola: generazione fallita" con il messaggio di errore nel body
- Richiedere il permesso notifiche al primo avvio

---

## Motore Python — Dettagli

### Stack

- Python 3.12+
- Dipendenze: `feedparser`, `python-docx`, `python-dateutil`
- Entry point: `engine/specola_engine.py`
- Moduli in `engine/src/`

### Struttura

```
engine/
├── specola_engine.py       # Entry point, argparse, orchestrazione
├── requirements.txt        # feedparser, python-docx, python-dateutil
├── setup_engine.sh         # Crea venv e installa dipendenze
├── src/
│   ├── __init__.py
│   ├── feed_fetcher.py     # Parsing OPML + fetch RSS concorrente
│   ├── prefilter.py        # Pre-filtering locale: rilevanza, dedup, troncamento
│   ├── analyzer.py         # Invocazione claude CLI via subprocess
│   ├── doc_generator.py    # Generazione DOCX con python-docx
│   └── prompt_builder.py   # Costruzione dinamica del prompt (ottimizzato token)
└── .work/                  # File intermedi (creata a runtime)
```

### CLI del motore

```
specola_engine.py run [opzioni]

--opml PATH              Path file OPML
--profile PATH           Path file profilo utente (profile.md)
--output-dir PATH        Directory output DOCX
--hours N                Finestra temporale (default: 24)
--language LANG          Lingua briefing: it/en (default: it)
--max-items N            Max item per categoria (default: 30)
--model MODEL            Modello Claude (opzionale)
--dry-run                Solo fetch, no Claude, no DOCX
--verbose                Logging DEBUG
```

Output: JSON su stdout (vedi sezione "Invocazione del motore Python" sopra). Logging su stderr.

### Vincolo critico: Claude Code CLI, non API

L'analisi passa dalla CLI di Claude Code via `subprocess`:

```bash
claude -p "prompt" < feed_digest.md
```

Non usare mai `import anthropic`, `ANTHROPIC_API_KEY`, o chiamate HTTP dirette.

Se `claude` non è nel PATH: restituire errore JSON. Timeout: 300 secondi. Se fallisce: generare DOCX dal digest grezzo con avviso.

### Feed Fetcher

#### Parsing OPML
- `xml.etree.ElementTree`
- `<outline>` primo livello = categoria
- Figli con `type="rss"` = feed
- Strippare prefissi numerici ("01 – " → "")
- Dict ordinato per nome

#### Fetch RSS
- `feedparser.parse(url)` con User-Agent `"Specola/1.0"`
- `ThreadPoolExecutor`, max 20 worker
- Timeout 15 secondi per feed
- Feed che falliscono: log debug su stderr, nessun errore fatale
- Filtro: solo item nelle ultime N ore (timezone-aware UTC)
- Data: `published_parsed` → `updated_parsed` → `dateutil.parser.parse`
- Data non determinabile: includere l'item
- Summary: `entry.summary` → `entry.description` → `entry.content[0].value`
- Strip HTML: regex `<[^>]+>`, `html.unescape()`, collassare whitespace
- Truncare summary a 500 caratteri (il pre-filter poi lo tronca a 200 per il LLM)
- Max N item per categoria, ordinati per data decrescente

#### FeedItem

```python
{
    "title": str,
    "link": str,
    "published": str,       # "YYYY-MM-DD HH:MM" o "data n/d"
    "summary": str,         # Plaintext, max 500 chars (200 dopo pre-filter)
    "source": str,          # Nome del feed
}
```

### Pre-filter (prefilter.py) — Ottimizzazione token

Prima di inviare qualsiasi dato al LLM, il pre-filter applica tre operazioni locali per ridurre il consumo di token del 60-75%:

#### 1. Keyword relevance scoring
- Estrae keyword dal profilo utente (tokenizzazione, rimozione stopword IT/EN)
- Calcola score di rilevanza per ogni item (Jaccard-like, titolo pesato 2x)
- Rimuove item sotto soglia, mantenendo almeno 3 per categoria
- Effetto: elimina 40-60% degli item irrilevanti

#### 2. Deduplicazione cross-feed
- Confronto Jaccard sui titoli normalizzati (soglia 0.6)
- Tiene il primo occorrimento (per data)
- Effetto: elimina 10-20% di duplicati

#### 3. Troncamento summary
- Tronca i summary a 200 caratteri (da 500) per il consumo LLM
- Taglia all'ultimo spazio per non spezzare parole

#### 4. Rimozione categorie vuote
- Categorie con 0 item dopo il filtro vengono rimosse (nessuna chiamata LLM)

### Batching categorie piccole

Categorie con meno di 5 item vengono raggruppate in una singola chiamata LLM anziché una per categoria. Questo evita il costo fisso del prompt (profilo + istruzioni) ripetuto per ogni micro-categoria.

### Formato digest compatto

Il digest inviato al LLM usa un formato compatto (`compact=True`) che risparmia ~30% di token rispetto al formato markdown verbose:

```
## Categoria
- **Titolo** (Fonte) https://link
  Summary breve troncato a 200 char
```

### Prompt Builder

Assembla il prompt da tre parti, ottimizzate per concisione:

#### 1. Istruzione di sistema (fissa, concisa)

```
Sei Specola, analista che produce briefing giornalieri da fonti RSS.
Analizza il digest, prioritizza per il profilo utente, produci analisi
strutturata. Per ogni notizia includi il link [testo](url).
Spiega contesto, implicazioni e rilevanza per l'utente.
```

#### 2. Profilo utente (da profile.md, iniettato così com'è)

```
Profilo utente:
{contenuto di profile.md}
```

#### 3. Istruzioni di output (compatte)

Per italiano (`it`):
```
Analizza le notizie della categoria "{category}".

Per ogni notizia: paragrafo di 3-4 frasi con implicazioni, trend e
rilevanza per l'utente. Formato:

**Titolo** — analisi. [Fonte](url)

Regole: italiano, zero fuffa, ogni item ha link, ordine per rilevanza,
ometti irrilevanti, non inventare.
```

Fase di sintesi — produce solo le sezioni trasversali:

```
## Da sapere oggi
5-7 punti trasversali. Per ciascuno: 2-3 frasi con contesto e [link](url).

## Richiede attenzione
Sviluppi che richiedono azione entro la settimana. 3-5 frasi: cosa, perché, cosa fare. Se non c'è nulla, ometti.

## Per area tematica
Per ogni categoria del digest che contiene notizie rilevanti, crea una sezione
H2 con il nome della categoria. Dentro: item ordinati per rilevanza, sintesi di
una o due frasi ciascuno, fonte tra parentesi. Ometti categorie senza notizie rilevanti.

## Da leggere con calma
Articoli di approfondimento non urgenti ma di valore.

## Spunti
2-3 idee per riflessioni, post, o azioni ispirate dalle notizie del giorno.

Regole:
- Scrivi in italiano
- Zero fuffa, zero premesse
- Ogni item ha la fonte tra parentesi
- Sezioni vuote: omettile
- Ordine per rilevanza decrescente
- Non inventare notizie assenti dal digest
- Max 3000 parole
```

Per inglese (`en`): stessa struttura tradotta, come seconda costante stringa. Non usare traduzione dinamica.

In coda: elenco categorie presenti nel digest.

### Analyzer

```python
import subprocess

def analyze_with_claude(digest_path: Path, prompt: str, model: str | None = None, timeout: int = 300) -> str | None:
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])

    with open(digest_path, "r") as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        return None
    return result.stdout
```

Pattern esatto. Non aggiungere retry, backoff, parsing JSON.

### Generazione DOCX

`python-docx`. Formattazione:

- A4, margini 2.5cm
- Calibri 11pt, interlinea 1.15
- H1: 18pt bold #1a1a2e, spacing before 18pt after 6pt
- H2: 14pt bold #16213e, spacing before 14pt after 4pt
- H3: 12pt bold #0f3460, spacing before 10pt after 4pt
- Paragrafi: spacing after 6pt
- Header: "Specola" a sinistra, data a destra, 9pt grigio
- Footer: numero pagina centrato, 9pt grigio
- File: `Specola_YYYY-MM-DD.docx`

Parsing markdown → DOCX riga per riga con regex:
- `# ` → Heading 1
- `## ` → Heading 2
- `### ` → Heading 3
- `- ` / `* ` → `List Bullet`
- `**testo**` → bold run
- `1. ` → `List Number`
- Righe vuote → separatore
- Resto → paragrafo

Non importare librerie di parsing markdown.

Fallback: DOCX dal digest grezzo con paragrafo rosso "⚠ Analisi non disponibile."

---

## Setup e distribuzione

### Struttura del progetto Xcode

```
Specola/
├── Specola.xcodeproj
├── Specola/
│   ├── SpecolaApp.swift          # @main, MenuBarExtra
│   ├── MenuBarView.swift         # Popover content
│   ├── SettingsView.swift        # Finestra settings (tabs)
│   ├── Models/
│   │   ├── SpecolaEntry.swift    # Modello singola Specola (history)
│   │   ├── AppState.swift        # Stato app (ObservableObject)
│   │   └── Settings.swift        # Wrapper UserDefaults
│   ├── Services/
│   │   ├── EngineService.swift   # Lancio motore Python
│   │   ├── SchedulerService.swift # Timer + wake detection
│   │   └── NotificationService.swift
│   ├── Assets.xcassets
│   └── Info.plist
├── engine/                        # Motore Python (bundled)
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

### Prima installazione

L'app al primo avvio deve:
1. Verificare se il venv Python esiste in `Application Support/Specola/engine/.venv/`
2. Se no: copiare la directory `engine/` bundled in Application Support e lanciare `setup_engine.sh` (crea venv, installa dipendenze)
3. Verificare se `claude` è nel PATH (controllare `/usr/local/bin/claude`, `~/.local/bin/claude`, `~/.claude/local/claude` e il PATH di sistema)
4. Se `claude` non trovata: mostrare un alert con istruzioni di installazione, ma non bloccare l'app (l'utente potrebbe voler configurare prima le fonti)

### setup_engine.sh

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## Cosa NON fare

- Non usare Electron, Tauri, o wrapper web
- Non usare SwiftPM packages per RSS (feedparser Python è più affidabile)
- Non creare un pacchetto PyPI per il motore
- Non usare `click`, `typer`, `rich`, `colorama` nel motore Python
- Non aggiungere retry o exponential backoff
- Non fare scraping di pagine web (solo RSS)
- Non usare async/await in Python (thread bastano)
- Non importare `anthropic` né chiamare API direttamente
- Non usare template engine (Jinja, Mako) per il prompt
- Non usare Core Data (overkill per questa app, JSON basta)
- Non usare launchd per lo scheduling (gestito internamente)
- Non creare un DMG o installer — per ora l'app si builda da Xcode
