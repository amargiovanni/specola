"""Tests for the pre-filtering module (relevance, dedup, truncation)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prefilter import (
    extract_profile_keywords,
    condense_profile,
    score_item,
    filter_by_relevance,
    deduplicate_items,
    truncate_summaries,
    prefilter_items,
)


# ── Profile keyword extraction ───────────────────────────────────────────

class TestExtractProfileKeywords:
    def test_extracts_meaningful_words(self):
        kw = extract_profile_keywords("Sono CTO di una startup fintech. Stack: Node.js, TypeScript, AWS.")
        assert "fintech" in kw
        assert "typescript" in kw
        assert "node" in kw or "node.js" in kw
        assert "startup" in kw

    def test_excludes_stopwords(self):
        kw = extract_profile_keywords("Sono il CTO di una startup")
        assert "sono" not in kw
        assert "una" not in kw

    def test_excludes_short_words(self):
        kw = extract_profile_keywords("I am a CTO at an AI company")
        assert "am" not in kw
        assert "at" not in kw

    def test_empty_profile(self):
        kw = extract_profile_keywords("")
        assert kw == set()

    def test_returns_set(self):
        kw = extract_profile_keywords("fintech fintech fintech")
        assert isinstance(kw, set)
        assert "fintech" in kw


# ── Profile condensation ─────────────────────────────────────────────────

class TestCondenseProfile:
    def test_returns_keywords_string(self):
        result = condense_profile("Sono CTO di una startup fintech. Stack: Node.js, TypeScript, AWS.")
        assert result.startswith("Keywords: ")
        assert "fintech" in result
        assert "TypeScript" in result

    def test_preserves_original_casing(self):
        result = condense_profile("Stack: TypeScript, AWS Lambda, PostgreSQL")
        # Should recover original capitalization
        assert "TypeScript" in result
        assert "AWS" in result
        assert "PostgreSQL" in result

    def test_empty_profile_returns_empty(self):
        assert condense_profile("") == ""
        assert condense_profile("   ") == ""

    def test_shorter_than_original(self):
        profile = "Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS Lambda, PostgreSQL. Mi interessa: regolamentazione EU, sicurezza API, trend VC europeo."
        condensed = condense_profile(profile)
        assert len(condensed) < len(profile)

    def test_deterministic(self):
        profile = "TypeScript AWS fintech startup"
        r1 = condense_profile(profile)
        r2 = condense_profile(profile)
        assert r1 == r2

    def test_sorted_alphabetically(self):
        result = condense_profile("zebra alpha middle")
        # Extract keywords after "Keywords: "
        keywords_part = result.replace("Keywords: ", "")
        keywords = [k.strip() for k in keywords_part.split(",")]
        assert keywords == sorted(keywords, key=lambda s: s.lower())

    def test_excludes_stopwords(self):
        result = condense_profile("Sono il responsabile della sicurezza")
        assert "sono" not in result.lower().split(", ")
        assert "della" not in result.lower().split(", ")

    def test_none_like_profile(self):
        # Profile with only stopwords/short words
        result = condense_profile("I am a the")
        # Should return the original text if no keywords extracted
        assert result == "I am a the"


# ── Relevance scoring ────────────────────────────────────────────────────

class TestScoreItem:
    def test_relevant_item_scores_high(self):
        keywords = {"fintech", "typescript", "aws", "startup"}
        item = {"title": "New TypeScript framework for fintech", "summary": "AWS integration included"}
        score = score_item(item, keywords)
        assert score > 0.1

    def test_irrelevant_item_scores_low(self):
        keywords = {"fintech", "typescript", "aws", "startup"}
        item = {"title": "Best recipes for pasta", "summary": "Italian cuisine tips"}
        score = score_item(item, keywords)
        assert score < 0.05

    def test_empty_profile_returns_one(self):
        score = score_item({"title": "Anything", "summary": "Whatever"}, set())
        assert score == 1.0

    def test_title_weighted_more(self):
        # Use a larger keyword set so scores don't clamp to 1.0
        keywords = {"fintech", "typescript", "aws", "node", "startup", "cloud", "api"}
        title_match = {"title": "Fintech revolution", "summary": "General news"}
        summary_match = {"title": "General news", "summary": "Fintech revolution"}
        assert score_item(title_match, keywords) > score_item(summary_match, keywords)


# ── Filter by relevance ──────────────────────────────────────────────────

class TestFilterByRelevance:
    def test_filters_irrelevant_items(self):
        keywords = {"fintech", "typescript", "aws"}
        items = [
            {"title": "TypeScript 6.0 released", "summary": "Major update for fintech devs"},
            {"title": "Best pasta recipes", "summary": "Italian cuisine"},
            {"title": "AWS Lambda price drop", "summary": "Cloud computing"},
        ]
        result = filter_by_relevance(items, keywords, min_score=0.02, keep_min=1)
        titles = [i["title"] for i in result]
        assert "TypeScript 6.0 released" in titles
        assert "AWS Lambda price drop" in titles

    def test_keeps_minimum_items(self):
        keywords = {"quantum_computing_xyz"}  # Won't match anything
        items = [
            {"title": "News A", "summary": "Something"},
            {"title": "News B", "summary": "Something else"},
        ]
        result = filter_by_relevance(items, keywords, min_score=0.5, keep_min=2)
        assert len(result) >= 2

    def test_empty_keywords_keeps_all(self):
        items = [{"title": "A", "summary": "B"}, {"title": "C", "summary": "D"}]
        result = filter_by_relevance(items, set())
        assert len(result) == 2

    def test_empty_items(self):
        result = filter_by_relevance([], {"fintech"})
        assert result == []


# ── Deduplication ────────────────────────────────────────────────────────

class TestDeduplicateItems:
    def test_removes_exact_duplicates(self):
        items = [
            {"title": "OpenAI releases GPT-5", "source": "TechCrunch"},
            {"title": "OpenAI releases GPT-5", "source": "Ars Technica"},
        ]
        result = deduplicate_items(items)
        assert len(result) == 1
        assert result[0]["source"] == "TechCrunch"  # Keeps first

    def test_removes_near_duplicates(self):
        items = [
            {"title": "OpenAI releases GPT-5 today", "source": "A"},
            {"title": "OpenAI releases GPT-5", "source": "B"},
        ]
        result = deduplicate_items(items, threshold=0.6)
        assert len(result) == 1

    def test_keeps_different_items(self):
        items = [
            {"title": "OpenAI releases GPT-5", "source": "A"},
            {"title": "EU passes new AI regulation", "source": "B"},
        ]
        result = deduplicate_items(items)
        assert len(result) == 2

    def test_empty_list(self):
        assert deduplicate_items([]) == []

    def test_single_item(self):
        items = [{"title": "Only one"}]
        assert deduplicate_items(items) == items

    def test_empty_titles_not_deduped(self):
        items = [{"title": ""}, {"title": ""}]
        result = deduplicate_items(items)
        assert len(result) == 2


# ── Summary truncation ───────────────────────────────────────────────────

class TestTruncateSummaries:
    def test_truncates_long_summaries(self):
        items = [{"summary": "word " * 100}]
        result = truncate_summaries(items, max_length=50)
        assert len(result[0]["summary"]) <= 55  # 50 + ellipsis + word boundary

    def test_keeps_short_summaries(self):
        items = [{"summary": "Short text"}]
        result = truncate_summaries(items, max_length=200)
        assert result[0]["summary"] == "Short text"

    def test_adds_ellipsis(self):
        items = [{"summary": "a " * 200}]
        result = truncate_summaries(items, max_length=20)
        assert result[0]["summary"].endswith("…")

    def test_empty_summary(self):
        items = [{"summary": ""}]
        result = truncate_summaries(items, max_length=200)
        assert result[0]["summary"] == ""


# ── Full pipeline ────────────────────────────────────────────────────────

class TestPrefilterItems:
    def test_reduces_item_count(self):
        profile = "CTO startup fintech TypeScript AWS Node.js"
        items = {
            "Tech": [
                {"title": "TypeScript 6.0", "summary": "New features for developers", "source": "A", "link": "", "published": ""},
                {"title": "Best pasta recipe", "summary": "Italian cuisine guide", "source": "B", "link": "", "published": ""},
                {"title": "AWS Lambda update", "summary": "Cloud computing pricing", "source": "C", "link": "", "published": ""},
            ],
            "Cooking": [
                {"title": "Michelin guide 2026", "summary": "New star restaurants", "source": "D", "link": "", "published": ""},
            ],
        }
        result = prefilter_items(items, profile)
        total_after = sum(len(v) for v in result.values())
        total_before = sum(len(v) for v in items.values())
        # Should have fewer items (cooking removed or reduced)
        assert total_after <= total_before

    def test_removes_empty_categories(self):
        profile = "fintech developer TypeScript"
        items = {
            "Tech": [
                {"title": "TypeScript update", "summary": "New release", "source": "A", "link": "", "published": ""},
            ],
            "Empty": [],
        }
        result = prefilter_items(items, profile)
        assert "Empty" not in result

    def test_deduplicates_within_category(self):
        profile = "tech news"
        items = {
            "Tech": [
                {"title": "OpenAI releases GPT-5", "summary": "Big news", "source": "A", "link": "", "published": ""},
                {"title": "OpenAI releases GPT-5", "summary": "Same news", "source": "B", "link": "", "published": ""},
            ],
        }
        result = prefilter_items(items, profile)
        assert len(result["Tech"]) == 1

    def test_truncates_summaries(self):
        profile = "tech"
        long_summary = "x " * 300
        items = {
            "Tech": [
                {"title": "News", "summary": long_summary, "source": "A", "link": "", "published": ""},
            ],
        }
        result = prefilter_items(items, profile)
        assert len(result["Tech"][0]["summary"]) < len(long_summary)

    def test_empty_input(self):
        result = prefilter_items({}, "any profile")
        assert result == {}

    def test_empty_profile_keeps_items(self):
        items = {
            "Tech": [
                {"title": "News", "summary": "Something", "source": "A", "link": "", "published": ""},
            ],
        }
        result = prefilter_items(items, "")
        assert "Tech" in result
        assert len(result["Tech"]) == 1
