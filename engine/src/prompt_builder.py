"""Prompt construction for Claude analysis."""
from __future__ import annotations

SYSTEM_INSTRUCTION = (
    "Sei Specola, un assistente che produce briefing giornalieri da fonti RSS.\n"
    "Analizza il digest in input, prioritizza le notizie in base al profilo\n"
    "dell'utente, e produci un briefing strutturato e approfondito."
)

OUTPUT_INSTRUCTIONS_IT = """\
Produci il briefing in markdown:

# Specola — Briefing del {date}

## Da sapere oggi
3-5 punti. Le cose più importanti per il profilo dell'utente. Una riga ciascuno.

## Richiede attenzione
Sviluppi che richiedono azione o valutazione entro la settimana. Per ciascuno: \
cosa è successo, perché conta per l'utente, cosa fare. Se non c'è nulla, ometti.

## Per area tematica
Per ogni categoria del digest che contiene notizie rilevanti, crea una sezione \
H2 con il nome della categoria. Dentro: item ordinati per rilevanza, sintesi di \
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
- Max 3000 parole"""

OUTPUT_INSTRUCTIONS_EN = """\
Produce the briefing in markdown:

# Specola — Briefing for {date}

## Must know today
3-5 points. The most important things for the user's profile. One line each.

## Needs attention
Developments that require action or evaluation within the week. For each: \
what happened, why it matters for the user, what to do. If nothing qualifies, omit.

## By topic
For each digest category that contains relevant news, create an H2 section \
with the category name. Inside: items ordered by relevance, one or two sentence \
summary each, source in parentheses. Omit categories with no relevant news.

## Deep reads
In-depth articles that are not urgent but valuable.

## Ideas
2-3 ideas for reflections, posts, or actions inspired by today's news.

Rules:
- Write in English
- Zero fluff, zero preamble
- Every item has its source in parentheses
- Empty sections: omit them
- Order by decreasing relevance
- Do not invent news absent from the digest
- Max 3000 words"""


def build_prompt(profile: str, language: str, categories: list[str], date: str) -> str:
    """Assemble complete prompt from system instruction, profile, and output instructions."""
    output_instructions = OUTPUT_INSTRUCTIONS_EN if language == "en" else OUTPUT_INSTRUCTIONS_IT

    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "Profilo dell'utente:",
        "---",
        profile,
        "---",
        "",
        output_instructions.format(date=date),
        "",
        "Categorie presenti nel digest:",
        *[f"- {cat}" for cat in categories],
    ]
    return "\n".join(parts)
