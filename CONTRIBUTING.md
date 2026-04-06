# Contributing to Specola

Specola accetta contributi. Questo documento definisce le regole — non sono suggerimenti.

Se una PR non le rispetta, viene rifiutata. Nessuna eccezione.

---

## Regola zero

**Non rompere quello che funziona.** Prima di aprire una PR, i test devono passare tutti. Sia Python che Swift. Se aggiungi codice, aggiungi test. Se modifichi comportamento, aggiorna i test.

---

## Sicurezza

### Vietato

- **Mai committare segreti.** Nessuna API key, token, password, certificato, `.env` file. Neanche in test, neanche come esempio, neanche commentati. Se un segreto finisce nella storia git, la PR viene rifiutata e il branch cancellato.
- **Mai usare `shell=True`** in `subprocess.run()` o `subprocess.Popen()`. Mai. Command injection è la vulnerabilità più banale e più pericolosa.
- **Mai costruire comandi CLI con string concatenation o f-string da input utente.** Usare sempre liste di argomenti: `["cmd", "--flag", value]`.
- **Mai usare `eval()`, `exec()`, `pickle.loads()` su dati non fidati.** Il motore Python processa feed RSS da Internet — tutto è untrusted.
- **Mai disabilitare verifiche TLS/SSL.** Nessun `verify=False`, nessun `ssl._create_unverified_context()`.
- **Mai loggare segreti.** Se un parametro contiene una API key, non deve finire su stderr neanche in modalità `--verbose`.

### Obbligatorio

- **Validare tutti i path** prima di scriverci. Verificare che siano dentro la directory di output attesa. Nessun path traversal.
- **Sanitizzare i nomi file** derivati da input esterno (titoli RSS, nomi categorie). Il motore usa `_SAFE_FILENAME_RE` — qualsiasi nuovo filename deve usarlo.
- **Timeout su tutte le chiamate di rete.** Nessun `urlopen()` senza `timeout=`. Nessun `subprocess.run()` senza `timeout=`. Mai.
- **Usare `html.escape()` o equivalente** quando si inietta testo da feed RSS in HTML. Il generatore HTML lo fa via `_inline_format()` — nuovi generatori devono fare lo stesso.

### Feed RSS = input ostile

I feed RSS vengono da Internet. Trattare ogni campo (`title`, `summary`, `link`, `content`) come potenzialmente malevolo:
- Strip HTML prima di usare il testo
- Non fidarsi mai di un URL senza validazione
- Non inserire mai testo raw in template HTML/XML senza escaping

---

## Qualità del codice

### Python

- **Python 3.12+.** Usare type hints su tutte le firme pubbliche.
- **Zero dipendenze nuove** senza approvazione esplicita. Il motore è volutamente leggero. Se pensi di aver bisogno di `requests`, `httpx`, `aiohttp` — no. Usa `urllib.request`. Se pensi di aver bisogno di `click` o `typer` — no. Usa `argparse`.
- **Nessun `import *`.** Mai.
- **Nessun `except Exception` nudo** in codice nuovo. Cattura l'eccezione specifica. I `# noqa: BLE001` esistenti nel codice legacy non sono un invito a farne di nuovi.
- **Nessun retry/backoff.** Specola non implementa retry automatici. Se un provider fallisce, fallisce. Il fallback è il digest grezzo. Questo è un design decision, non una dimenticanza.
- **Nessun async/await.** I thread bastano per l'I/O-bound RSS fetching. Non aggiungere `asyncio`, `aiohttp`, o event loop.
- **Nessun template engine.** Niente Jinja, Mako, o simili. Il prompt si costruisce con string join. L'HTML con string formatting. È una scelta consapevole.
- **Formattazione:** seguire lo stile esistente. Se non sei sicuro, guarda i file vicini. Non aggiungere docstring, commenti, o type annotation a codice che non hai modificato.
- **Max 120 caratteri per riga** (non 80, non 100 — 120).

### Swift

- **Swift 5.9+, macOS 14+ (Sonoma).**
- **Zero SPM packages** senza approvazione esplicita. SwiftUI, AppKit, WidgetKit, CoreSpotlight e il framework standard bastano.
- **`@Observable` (Observation), non `ObservableObject` (Combine).** Il progetto usa il nuovo macro-based observation. Non mescolare i due pattern.
- **UserDefaults per le impostazioni.** Non Core Data, non SwiftData, non SQLite. 30 entry JSON non giustificano un database.
- **Nessun `force unwrap`** (`!`) in codice nuovo tranne che nei test. Usare `guard let` o `if let`.
- **Nessun `print()`** in produzione. Usare `logger` (Python) o niente (Swift — le notifiche e il JSON parlano abbastanza).

### Architettura

- **L'app Swift non fa analisi.** Non importare `feedparser`, non parsare RSS in Swift, non invocare LLM da Swift. L'app Swift lancia il motore Python e legge il JSON di output. Punto.
- **Il motore Python non fa UI.** Non importare `AppKit`, `SwiftUI`, o qualsiasi framework Apple. Il motore è un CLI tool puro che scrive JSON su stdout e log su stderr.
- **Ogni modifica al contratto Swift↔Python** (argomenti CLI, formato JSON di output) deve aggiornare entrambi i lati E i test E il README.

---

## Test

### La regola è semplice

> **Se non ha test, non entra.**

Non esistono eccezioni. Non "lo aggiungo dopo". Non "è troppo semplice per testarlo". Non "è solo UI".

### Python (pytest)

- Ogni funzione pubblica ha almeno un test per il caso felice e uno per ogni caso di errore.
- I test devono poter girare **offline e senza LLM**. Tutte le chiamate esterne (Claude CLI, Codex CLI, LMStudio, feedparser) devono essere mockate.
- I mock vanno sul confine del modulo (`@patch("modulo.funzione")`), non su implementazioni interne.
- Usare `tmp_path` per file temporanei. Non scrivere in directory fisse.
- I test non devono dipendere dall'ordine di esecuzione.
- **Run:** `cd engine && python -m pytest tests/ -v --tb=short`
- **Attualmente: 367+ test.** Il numero sale, non scende.

### Swift (XCTest)

- Testare modelli, service, e logica. Non testare SwiftUI views direttamente (sono di competenza UI review).
- Non usare `XCTUnwrap` dove un `guard` + `XCTFail` è più chiaro.
- Pulire `UserDefaults` nei test che modificano `SpecolaSettings` — ogni test deve essere indipendente.
- **Run:** `xcodebuild test -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO`
- **Attualmente: 90+ test.** Il numero sale, non scende.

### CI

GitHub Actions gira su ogni push e PR. Due job:
- **python-tests**: Ubuntu, Python 3.12, tutti i pytest
- **swift-tests**: macOS 15, Xcode 16.4, tutti gli XCTest

Se CI è rosso, la PR non viene reviewata. Punto.

---

## Come contribuire

### 1. Apri un issue prima

Non partire a scrivere codice. Apri un issue descrivendo cosa vuoi fare e perché. Discutiamo l'approccio *prima* di scrivere una riga. Questo evita PR rifiutate dopo giorni di lavoro.

### 2. Un branch, una cosa

Un branch per feature/fix. Non mescolare "fix typo in README" con "aggiungi nuovo provider LLM". Se una PR tocca troppi file non correlati, viene rifiutata.

### 3. Scrivi test prima del codice

O almeno insieme al codice. La PR deve includere test per tutto il codice nuovo. Se modifichi codice esistente e scopri che non ha test, aggiungili — anche se non li hai rotti tu.

### 4. Messaggi di commit

```
tipo(scope): descrizione breve

Corpo opzionale con dettagli.
```

Tipi: `feat`, `fix`, `test`, `docs`, `refactor`, `ci`, `chore`. Scope opzionale. Descrizione in inglese, imperativo. Esempio:

```
feat(engine): add Gemini CLI provider support

Adds _analyze_gemini() subprocess wrapper and --provider gemini CLI arg.
```

### 5. Cosa includere nella PR description

- **Cosa** hai cambiato (non "vedi il diff" — descrivilo in parole)
- **Perché** l'hai cambiato
- **Come testarlo** (se non è ovvio dai test automatici)
- Riferimento all'issue: `Closes #N`

### 6. Non toccare ciò che non devi

- Non riformattare codice che non hai modificato
- Non aggiungere docstring/commenti a funzioni che non hai toccato
- Non cambiare indentazione, import order, o stile di codice esistente "per uniformità"
- Non aggiungere feature che nessuno ha chiesto

---

## Cosa non accettiamo

- PR senza test
- PR che rompono test esistenti
- PR che aggiungono dipendenze senza discussione nell'issue
- PR che toccano il contratto Swift↔Python senza aggiornare entrambi i lati
- PR che committano segreti, `.env`, credentials, o file binari
- PR "cosmetiche" che riformattano codice non modificato
- PR che aggiungono `// TODO`, `// FIXME`, `// HACK` senza un issue collegato
- PR generate interamente da AI senza review umana

---

## Licenza

Contribuendo a Specola, accetti che il tuo codice sia rilasciato sotto la stessa licenza MIT del progetto.
