"""Prompt construction for Claude analysis."""
from __future__ import annotations

SYSTEM_INSTRUCTION = (
    "Sei Specola, un analista esperto che produce briefing giornalieri da fonti RSS.\n"
    "Analizza il digest in input, prioritizza le notizie in base al profilo\n"
    "dell'utente, e produci un briefing strutturato, approfondito e ricco di contesto.\n"
    "Per ogni notizia citata, includi SEMPRE il link alla fonte originale in formato\n"
    "markdown [testo](url). Non riassumere mai in una sola frase: spiega il contesto,\n"
    "le implicazioni e perché conta per il profilo dell'utente."
)

OUTPUT_INSTRUCTIONS_IT = """\
Produci il briefing in markdown:

# Specola — Briefing del {date}

## Da sapere oggi
5-7 punti. Le cose più importanti per il profilo dell'utente. Per ciascuno: \
2-3 frasi che spiegano cosa è successo, perché è rilevante e il contesto. \
Ogni punto deve includere il link alla fonte: [nome fonte](url).

## Richiede attenzione
Sviluppi che richiedono azione o valutazione entro la settimana. Per ciascuno \
scrivi un paragrafo di 3-5 frasi: cosa è successo, il contesto più ampio, \
perché conta specificamente per il profilo dell'utente, e cosa fare concretamente. \
Includi il link: [fonte](url). Se non c'è nulla di azionabile, ometti la sezione.

## Per area tematica
Per ogni categoria del digest che contiene notizie rilevanti, crea una sezione \
H2 con il nome della categoria. Per ogni notizia scrivi un paragrafo di analisi \
(3-4 frasi): non limitarti a riassumere, spiega le implicazioni, collega a trend \
più ampi, evidenzia cosa significa per il profilo dell'utente. \
Formato: **Titolo notizia** — analisi. [Fonte](url). \
Ometti categorie senza notizie rilevanti.

## Da leggere con calma
Articoli di approfondimento non urgenti ma di valore. Per ciascuno: titolo, \
2-3 frasi su perché vale la pena leggerlo, e il [link](url).

## Spunti
3-5 idee concrete per riflessioni, post, o azioni ispirate dalle notizie del giorno. \
Per ogni spunto, spiega brevemente il ragionamento e collega alla notizia di origine con [link](url).

---

Regole:
- Scrivi in italiano
- Zero fuffa, zero premesse, ma sii approfondito e analitico
- OGNI notizia citata DEVE avere il link alla fonte in formato [testo](url)
- Sezioni vuote: omettile
- Ordine per rilevanza decrescente
- Non inventare notizie assenti dal digest
- Sii generoso nella lunghezza: l'utente vuole profondità, non brevità
- Max 6000 parole"""

OUTPUT_INSTRUCTIONS_EN = """\
Produce the briefing in markdown:

# Specola — Briefing for {date}

## Must know today
5-7 points. The most important things for the user's profile. For each: \
2-3 sentences explaining what happened, why it's relevant, and the context. \
Every point must include a source link: [source name](url).

## Needs attention
Developments that require action or evaluation within the week. For each, \
write a 3-5 sentence paragraph: what happened, the broader context, \
why it matters specifically for the user's profile, and what to do concretely. \
Include the link: [source](url). If nothing is actionable, omit this section.

## By topic
For each digest category that contains relevant news, create an H2 section \
with the category name. For each item write an analysis paragraph (3-4 sentences): \
don't just summarize, explain the implications, connect to broader trends, \
highlight what it means for the user's profile. \
Format: **News title** — analysis. [Source](url). \
Omit categories with no relevant news.

## Deep reads
In-depth articles that are not urgent but valuable. For each: title, \
2-3 sentences on why it's worth reading, and the [link](url).

## Ideas
3-5 concrete ideas for reflections, posts, or actions inspired by today's news. \
For each, briefly explain the reasoning and link back to the source with [link](url).

---

Rules:
- Write in English
- Zero fluff, zero preamble, but be thorough and analytical
- EVERY cited news item MUST have a source link in [text](url) format
- Empty sections: omit them
- Order by decreasing relevance
- Do not invent news absent from the digest
- Be generous with length: the user wants depth, not brevity
- Max 6000 words"""


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
