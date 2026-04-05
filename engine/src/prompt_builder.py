"""Prompt construction for Claude analysis — two-phase approach."""
from __future__ import annotations

SYSTEM_INSTRUCTION = (
    "Sei Specola, un analista esperto che produce briefing giornalieri da fonti RSS.\n"
    "Analizza il digest in input, prioritizza le notizie in base al profilo\n"
    "dell'utente, e produci un briefing strutturato, approfondito e ricco di contesto.\n"
    "Per ogni notizia citata, includi SEMPRE il link alla fonte originale in formato\n"
    "markdown [testo](url). Non riassumere mai in una sola frase: spiega il contesto,\n"
    "le implicazioni e perché conta per il profilo dell'utente."
)

# ── Phase 1: Per-category analysis ──

CATEGORY_INSTRUCTIONS_IT = """\
Analizza le seguenti notizie dalla categoria "{category}".

Per ogni notizia, scrivi un paragrafo analitico di 3-4 frasi:
- Non limitarti a riassumere: spiega le implicazioni e collega a trend più ampi
- Evidenzia cosa significa per il profilo dell'utente
- Includi il link alla fonte in formato [testo](url)

Formato per ogni item:

**Titolo notizia** — paragrafo di analisi. [Fonte](url)

Regole:
- Scrivi in italiano
- Zero fuffa, vai dritto al punto ma con profondità
- OGNI notizia DEVE avere il link alla fonte
- Ordine per rilevanza decrescente per il profilo dell'utente
- Ometti notizie irrilevanti per il profilo
- Non inventare notizie assenti dal digest"""

CATEGORY_INSTRUCTIONS_EN = """\
Analyze the following news items from the "{category}" category.

For each item, write an analytical paragraph of 3-4 sentences:
- Don't just summarize: explain implications and connect to broader trends
- Highlight what it means for the user's profile
- Include the source link in [text](url) format

Format for each item:

**News title** — analysis paragraph. [Source](url)

Rules:
- Write in English
- Zero fluff, get to the point but with depth
- EVERY item MUST have a source link
- Order by decreasing relevance for the user's profile
- Omit items irrelevant to the profile
- Do not invent news absent from the digest"""

# ── Phase 2: Synthesis ──

SYNTHESIS_INSTRUCTIONS_IT = """\
Hai ricevuto le analisi per categoria di un briefing giornaliero. \
Ora produci SOLO le sezioni trasversali, in markdown:

## Da sapere oggi
5-7 punti. Le cose più importanti TRASVERSALMENTE a tutte le categorie \
per il profilo dell'utente. Per ciascuno: 2-3 frasi con contesto e il \
link alla fonte [nome](url). Scegli da categorie diverse, non solo una.

## Richiede attenzione
Sviluppi che richiedono azione o valutazione entro la settimana. Per ciascuno \
3-5 frasi: cosa è successo, perché conta per l'utente, cosa fare concretamente. \
Link incluso. Se non c'è nulla di azionabile, ometti la sezione.

## Da leggere con calma
Articoli di approfondimento non urgenti ma di valore, da tutte le categorie. \
Per ciascuno: titolo, 2-3 frasi su perché vale la pena, e il [link](url).

## Spunti
3-5 idee concrete per riflessioni, post, o azioni ispirate dalle notizie del giorno. \
Per ogni spunto, spiega brevemente il ragionamento e collega alla notizia con [link](url).

Regole:
- Scrivi in italiano
- Produci SOLO queste sezioni, NON ripetere le analisi per categoria
- OGNI item citato DEVE avere il link alla fonte
- Non inventare notizie assenti dalle analisi
- Sii approfondito e analitico"""

SYNTHESIS_INSTRUCTIONS_EN = """\
You have received per-category analyses from a daily briefing. \
Now produce ONLY the cross-cutting sections, in markdown:

## Must know today
5-7 points. The most important things ACROSS all categories \
for the user's profile. For each: 2-3 sentences with context and \
source link [name](url). Pick from different categories, not just one.

## Needs attention
Developments that require action or evaluation within the week. For each \
3-5 sentences: what happened, why it matters for the user, what to do. \
Link included. If nothing is actionable, omit this section.

## Deep reads
In-depth articles that are not urgent but valuable, from all categories. \
For each: title, 2-3 sentences on why it's worth reading, and the [link](url).

## Ideas
3-5 concrete ideas for reflections, posts, or actions inspired by today's news. \
For each, briefly explain the reasoning and link back to the source with [link](url).

Rules:
- Write in English
- Produce ONLY these sections, do NOT repeat per-category analyses
- EVERY cited item MUST have a source link
- Do not invent news absent from the analyses
- Be thorough and analytical"""


def build_category_prompt(
    profile: str, language: str, category: str,
) -> str:
    """Build prompt for analyzing a single category."""
    instructions = (
        CATEGORY_INSTRUCTIONS_EN if language == "en" else CATEGORY_INSTRUCTIONS_IT
    )

    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "Profilo dell'utente:",
        "---",
        profile,
        "---",
        "",
        instructions.format(category=category),
    ]
    return "\n".join(parts)


def build_synthesis_prompt(
    profile: str, language: str, date: str,
) -> str:
    """Build prompt for the synthesis pass over all category analyses."""
    instructions = (
        SYNTHESIS_INSTRUCTIONS_EN if language == "en" else SYNTHESIS_INSTRUCTIONS_IT
    )

    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "Profilo dell'utente:",
        "---",
        profile,
        "---",
        "",
        f"Data del briefing: {date}",
        "",
        instructions,
    ]
    return "\n".join(parts)


# Keep for backward compatibility / dry-run
def build_prompt(profile: str, language: str, categories: list[str], date: str) -> str:
    """Legacy single-pass prompt. Used by dry-run and fallback."""
    return build_synthesis_prompt(profile, language, date)
