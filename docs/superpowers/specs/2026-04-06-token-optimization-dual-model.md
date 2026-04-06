# Specola — Token Optimization: Dual-Model + Condensed Profile

**Date:** 2026-04-06
**Status:** Implemented
**Branch:** `claude/token-optimization-fW8Ml`

---

## Summary

Two optimizations to reduce LLM token consumption by ~70-80%:

1. **Dual-model architecture** — per-category analysis (phase 1) uses a faster/cheaper model; cross-cutting synthesis (phase 2) uses the full-quality model.
2. **Condensed profile for phase 1** — the full user profile (~400+ tokens) is replaced by a keyword-only version (~50-80 tokens) in per-category calls. The full profile is reserved for synthesis.

---

## Problem

Before this change, every LLM call (N categories + 1 synthesis = N+1 calls) included:
- The **full user profile** verbatim (400+ tokens × N+1 calls = 3,200+ profile tokens for 8 categories)
- The **same model** for simple per-item analysis and complex cross-cutting synthesis

Per-category analysis is a simple task (read 5-30 RSS items, write 3-4 sentences each). It doesn't require top-tier reasoning. The profile is needed only for relevance judgment — keywords suffice.

---

## Solution

### 1. Dual-model (`--category-model`)

New CLI argument:

```
--category-model MODEL    Faster/cheaper model for per-category analysis (phase 1).
                          Falls back to --model if not set.
--model MODEL             Model for synthesis (phase 2). Also used for categories
                          if --category-model is not set.
```

**Precedence:**
- Phase 1 (categories): `--category-model` → `--model` → CLI default
- Phase 2 (synthesis): `--model` → CLI default

**Recommended configuration for Claude:**

| Phase | Model | Why |
|-------|-------|-----|
| Phase 1 (categories) | `claude-haiku-4-5-20251001` | Fast, cheap, sufficient for per-item analysis |
| Phase 2 (synthesis) | `claude-sonnet-4-6` | Better reasoning for cross-cutting insights |

Haiku is ~10x cheaper than Opus and ~3x faster. For the simple per-category task (extract implications from RSS items), it produces comparable quality.

**Example:**

```bash
.venv/bin/python specola_engine.py run \
    --opml ~/feeds.opml \
    --profile ~/profile.md \
    --output-dir ~/Documents/Specola \
    --model claude-sonnet-4-6 \
    --category-model claude-haiku-4-5-20251001
```

### 2. Condensed profile

A new function `condense_profile()` in `prefilter.py` extracts keywords from the user profile and formats them as a compact string:

**Input (full profile, ~400 tokens):**
> Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS Lambda, PostgreSQL. Mi interessa: regolamentazione EU (AI Act, PSD3, DORA), sicurezza API, trend VC europeo, open source. Sto valutando la migrazione a Bun. Progetti attivi: piattaforma di pagamenti B2B, integrazione con PagoPA.

**Output (condensed, ~50 tokens):**
> Keywords: API, AWS, Act, B2B, Bun, CTO, DORA, fintech, integrazione, Lambda, migrazione, Milano, Node, open, pagamenti, PagoPA, PSD3, PostgreSQL, regolamentazione, sicurezza, source, startup, trend, TypeScript

The condensed profile:
- Uses the existing `extract_profile_keywords()` (tokenization + stopword removal)
- Recovers original casing from the source text (preserves "TypeScript", "AWS", "PagoPA")
- Is deterministic and sorted alphabetically
- Is used only for phase 1 (per-category) calls
- Phase 2 (synthesis) always receives the full profile

---

## Changes

### Python engine

| File | Change |
|------|--------|
| `engine/src/prefilter.py` | Added `condense_profile()` function |
| `engine/src/prompt_builder.py` | `build_category_prompt()` accepts optional `compact_profile` parameter |
| `engine/specola_engine.py` | New `--category-model` CLI arg; `run_engine()` accepts `category_model`; `_analyze_categories()` accepts `category_model` and `compact_profile`; profile condensation logged |

### Swift app

| File | Change |
|------|--------|
| `Specola/Models/Settings.swift` | Added `claudeCategoryModel` and `claudeSynthesisModel` settings |
| `Specola/Services/EngineService.swift` | Passes `--model` and `--category-model` for Claude provider |
| `Specola/SettingsView.swift` | Claude provider section now shows "Modello sintesi" and "Modello categorie" text fields |

---

## Token savings estimate

| Optimization | Savings |
|---|---|
| Condensed profile (per-category) | ~60-70% of profile cost (repeated N times) |
| Haiku for phase 1 | ~75% cost reduction (Haiku is ~10x cheaper) |
| Combined (8 categories) | **~70-80% total cost reduction** |

**Concrete example** (8 categories, 400-token profile):

| Before | After |
|--------|-------|
| Profile: 400 tokens × 9 calls = 3,600 | Profile: 80 × 8 + 400 × 1 = 1,040 |
| Model: Opus × 9 calls | Model: Haiku × 8 + Sonnet × 1 |
| Estimated cost: ~$0.50/run | Estimated cost: ~$0.08/run |

---

## Backward compatibility

- `--category-model` is optional. If not set, phase 1 uses `--model` (same as before).
- `condense_profile` is always applied for phase 1. There is no opt-out, but the keyword extraction is lossless for relevance purposes.
- Swift settings default to empty strings (= use CLI defaults), so existing users see no change.
- The `--model` flag semantics are preserved: it remains the "main" model, now specifically for synthesis.

---

## Out of scope

- Output length cap (`--max-tokens`) on category calls — future optimization
- Synthesis input truncation (cap on concatenated category analyses) — future optimization
- Raising the pre-filter relevance threshold (`min_score`) — requires user testing
- Title truncation in pre-filter — minor token saving
