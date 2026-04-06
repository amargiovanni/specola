"""Prompt construction for Claude analysis — two-phase approach.

Optimized for token efficiency:
- Concise instructions (the LLM doesn't need verbose explanations)
- Profile injected once per call (unavoidable, but kept lean)
- Category instructions are tight and action-oriented
"""
from __future__ import annotations

SYSTEM_INSTRUCTION = (
    "Sei Specola, analista che produce briefing giornalieri da fonti RSS. "
    "Analizza il digest, prioritizza per il profilo utente, produci analisi "
    "strutturata. Per ogni notizia includi il link [testo](url). "
    "Spiega contesto, implicazioni e rilevanza per l'utente."
)

# ── Phase 1: Per-category analysis ──

CATEGORY_INSTRUCTIONS_IT = """\
Analizza le notizie della categoria "{category}".

Per ogni notizia: paragrafo di 3-4 frasi con implicazioni, trend e rilevanza per l'utente. Formato:

**Titolo** — analisi. [Fonte](url)

Regole: italiano, zero fuffa, ogni item ha link, ordine per rilevanza, ometti irrilevanti, non inventare."""

CATEGORY_INSTRUCTIONS_EN = """\
Analyze news from "{category}".

Per item: 3-4 sentence analytical paragraph with implications, trends, relevance. Format:

**Title** — analysis. [Source](url)

Rules: English, zero fluff, every item has link, order by relevance, omit irrelevant, don't invent."""

# ── Phase 2: Synthesis ──

SYNTHESIS_INSTRUCTIONS_IT = """\
Dalle analisi per categoria, produci SOLO queste sezioni markdown:

## Da sapere oggi
5-7 punti trasversali. Per ciascuno: 2-3 frasi con contesto e [link](url). Categorie diverse.

## Richiede attenzione
Sviluppi che richiedono azione entro la settimana. 3-5 frasi: cosa, perché, cosa fare. Link. Se nulla, ometti.

## Da leggere con calma
Approfondimenti non urgenti di valore. Titolo, 2-3 frasi, [link](url).

## Spunti
3-5 idee concrete per riflessioni o azioni. Ragionamento breve + [link](url).

Regole: italiano, SOLO queste sezioni, ogni item ha link, non inventare, sii analitico."""

SYNTHESIS_INSTRUCTIONS_EN = """\
From the per-category analyses, produce ONLY these markdown sections:

## Must know today
5-7 cross-cutting points. Each: 2-3 sentences with context and [link](url). Diverse categories.

## Needs attention
Developments requiring action this week. 3-5 sentences: what, why, what to do. Link. If nothing, omit.

## Deep reads
Non-urgent valuable articles. Title, 2-3 sentences, [link](url).

## Ideas
3-5 concrete ideas for reflections or actions. Brief reasoning + [link](url).

Rules: English, ONLY these sections, every item has link, don't invent, be analytical."""


def build_category_prompt(
    profile: str, language: str, category: str,
    compact_profile: str | None = None,
) -> str:
    """Build prompt for analyzing a single category (or batched categories).

    If compact_profile is provided, it is used instead of the full profile
    to reduce token usage. The full profile is reserved for synthesis.
    """
    instructions = (
        CATEGORY_INSTRUCTIONS_EN if language == "en" else CATEGORY_INSTRUCTIONS_IT
    )

    effective_profile = compact_profile if compact_profile else profile

    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "Profilo utente:",
        effective_profile,
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
        "Profilo utente:",
        profile,
        "",
        f"Data: {date}",
        "",
        instructions,
    ]
    return "\n".join(parts)


# Keep for backward compatibility / dry-run
def build_prompt(profile: str, language: str, categories: list[str], date: str) -> str:
    """Legacy single-pass prompt. Used by dry-run and fallback."""
    return build_synthesis_prompt(profile, language, date)
