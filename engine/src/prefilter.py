"""Local pre-filtering to reduce LLM token usage.

Three strategies applied before sending anything to the LLM:
1. Keyword-based relevance scoring against user profile
2. Cross-feed deduplication by title similarity
3. Summary truncation for compactness
"""
from __future__ import annotations

import logging
import re
import unicodedata
from collections import Counter

logger = logging.getLogger("specola.prefilter")

# ── Helpers ──────────────────────────────────────────────────────────────

_WORD_RE = re.compile(r"[a-zà-öø-ÿ0-9]{3,}", re.IGNORECASE)
_STOPWORDS_IT = frozenset(
    "che con del della delle dei degli del della delle "
    "per una uno gli nel nella nei sono non più anche come "
    "questo questa questi queste stato stati essere "
    "sua suo suoi sue loro tutti tutto ogni altra altre "
    "altri dopo prima tra fra solo ancora già verso fino "
    "quando dove perché quale quali molto molta molti "
    "era hanno fatto fare può dalla dalle degli dallo "
    "dal alla alle allo alle".split()
)
_STOPWORDS_EN = frozenset(
    "the and for are but not you all any can had her was one our "
    "out has its how who did get let say she too use from into "
    "that with this will have been than they each make like long "
    "many over such take them than these some what when which your "
    "about after could other their there would been more also most "
    "just than very where those being through should between before".split()
)
_STOPWORDS = _STOPWORDS_IT | _STOPWORDS_EN


def _tokenize(text: str) -> list[str]:
    """Extract lowercase word tokens, removing stopwords and short words."""
    words = _WORD_RE.findall(text.lower())
    return [w for w in words if w not in _STOPWORDS]


def _normalize_title(title: str) -> str:
    """Normalize title for dedup comparison."""
    t = unicodedata.normalize("NFKD", title.lower().strip())
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ── Profile keyword extraction ───────────────────────────────────────────

def extract_profile_keywords(profile_text: str) -> set[str]:
    """Extract meaningful keywords from the user profile.

    Returns a set of lowercase tokens that represent the user's interests,
    role, stack, and domain.
    """
    tokens = _tokenize(profile_text)
    # Weight tokens by frequency — words repeated in the profile are more important
    counts = Counter(tokens)
    # Keep all unique tokens (even freq=1 matter in a profile)
    return set(counts.keys())


def condense_profile(profile_text: str) -> str:
    """Produce a compact keyword-only version of the user profile.

    Used for per-category LLM calls where the full profile text would waste
    tokens. The full profile is reserved for the synthesis pass.

    A 400-token profile typically condenses to ~50-80 tokens.
    """
    if not profile_text or not profile_text.strip():
        return ""

    keywords = extract_profile_keywords(profile_text)
    if not keywords:
        return profile_text.strip()

    # Sort for deterministic output; capitalize proper-looking tokens
    # Recover original casing from the source text for better LLM comprehension
    original_tokens = _WORD_RE.findall(profile_text)
    # Build a map: lowercase → best original form (prefer capitalized/original)
    casing: dict[str, str] = {}
    for tok in original_tokens:
        low = tok.lower()
        if low in keywords:
            # Prefer forms that start uppercase or contain dots (e.g. Node.js)
            if low not in casing or tok[0].isupper():
                casing[low] = tok

    # Use original casing where available, else lowercase
    display = sorted(
        (casing.get(kw, kw) for kw in keywords),
        key=lambda s: s.lower(),
    )

    return "Keywords: " + ", ".join(display)


# ── Relevance scoring ────────────────────────────────────────────────────

def score_item(item: dict, profile_keywords: set[str]) -> float:
    """Score a feed item's relevance to the user profile.

    Returns a score between 0.0 and 1.0.
    Title matches are weighted 2x vs summary matches.
    """
    title_tokens = set(_tokenize(item.get("title", "")))
    summary_tokens = set(_tokenize(item.get("summary", "")))

    if not profile_keywords:
        return 1.0  # No profile = keep everything

    # Title overlap (weighted 2x)
    title_overlap = len(title_tokens & profile_keywords)
    # Summary overlap
    summary_overlap = len(summary_tokens & profile_keywords)

    # Weighted score normalized by profile size
    raw = (title_overlap * 2 + summary_overlap) / max(len(profile_keywords), 1)
    # Clamp to [0, 1]
    return min(raw, 1.0)


def filter_by_relevance(
    items: list[dict],
    profile_keywords: set[str],
    min_score: float = 0.02,
    keep_min: int = 3,
) -> list[dict]:
    """Filter items by relevance to profile, keeping at least keep_min.

    Args:
        items: List of FeedItem dicts.
        profile_keywords: Keywords extracted from user profile.
        min_score: Minimum relevance score to keep an item.
        keep_min: Always keep at least this many items (top scored).

    Returns:
        Filtered list of items, preserving original order.
    """
    if not profile_keywords or not items:
        return items

    scored = [(item, score_item(item, profile_keywords)) for item in items]

    # Keep items above threshold
    above = [(item, s) for item, s in scored if s >= min_score]

    if len(above) >= keep_min:
        return [item for item, _ in above]

    # If too few pass the threshold, keep the top-scored ones
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:keep_min]
    # Preserve original order
    top_items = {id(item) for item, _ in top}
    return [item for item in items if id(item) in top_items]


# ── Deduplication ────────────────────────────────────────────────────────

def deduplicate_items(items: list[dict], threshold: float = 0.6) -> list[dict]:
    """Remove near-duplicate items based on title similarity.

    Keeps the first occurrence (by list order, which is date-sorted).
    Uses Jaccard similarity on title word sets.

    Args:
        items: List of FeedItem dicts (pre-sorted by date desc).
        threshold: Jaccard similarity threshold for considering duplicates.

    Returns:
        Deduplicated list preserving order.
    """
    if len(items) <= 1:
        return items

    seen_titles: list[set[str]] = []
    result: list[dict] = []

    for item in items:
        title_words = set(_normalize_title(item.get("title", "")).split())
        if not title_words:
            result.append(item)
            continue

        is_dup = False
        for seen in seen_titles:
            if _jaccard(title_words, seen) >= threshold:
                is_dup = True
                logger.debug("Dedup: dropped '%s'", item.get("title", "")[:60])
                break

        if not is_dup:
            seen_titles.append(title_words)
            result.append(item)

    dropped = len(items) - len(result)
    if dropped > 0:
        logger.info("Dedup: removed %d duplicate items", dropped)
    return result


# ── Summary truncation ───────────────────────────────────────────────────

def truncate_summaries(items: list[dict], max_length: int = 200) -> list[dict]:
    """Truncate item summaries to save tokens.

    Modifies items in-place and returns them.
    """
    for item in items:
        summary = item.get("summary", "")
        if len(summary) > max_length:
            # Cut at last space before limit to avoid broken words
            cut = summary[:max_length].rsplit(" ", 1)[0]
            item["summary"] = cut + "…"
    return items


# ── Main pipeline ────────────────────────────────────────────────────────

def prefilter_items(
    items_by_category: dict[str, list[dict]],
    profile_text: str,
) -> dict[str, list[dict]]:
    """Apply the full pre-filtering pipeline to all categories.

    Steps:
    1. Extract profile keywords
    2. Per category: deduplicate → filter by relevance → truncate summaries
    3. Remove empty categories

    Returns:
        Filtered dict (categories with 0 items are removed).
    """
    profile_keywords = extract_profile_keywords(profile_text)
    logger.info(
        "Profile keywords: %d unique terms extracted",
        len(profile_keywords),
    )

    total_before = sum(len(items) for items in items_by_category.values())
    result: dict[str, list[dict]] = {}

    for category, items in items_by_category.items():
        if not items:
            continue

        before = len(items)
        # Step 1: Dedup within category
        items = deduplicate_items(items)
        # Step 2: Relevance filter
        items = filter_by_relevance(items, profile_keywords)
        # Step 3: Truncate summaries
        items = truncate_summaries(items)

        if items:
            result[category] = items
            logger.debug(
                "  %s: %d → %d items", category, before, len(items)
            )

    total_after = sum(len(items) for items in result.values())
    cats_removed = len(items_by_category) - len(result)
    logger.info(
        "Pre-filter: %d → %d items (%.0f%% reduction), %d empty categories removed",
        total_before, total_after,
        (1 - total_after / max(total_before, 1)) * 100,
        cats_removed,
    )

    return result
