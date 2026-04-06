from src.prompt_builder import (
    build_category_prompt,
    build_synthesis_prompt,
    build_prompt,
    SYSTEM_INSTRUCTION,
    CATEGORY_INSTRUCTIONS_IT,
    CATEGORY_INSTRUCTIONS_EN,
    SYNTHESIS_INSTRUCTIONS_IT,
    SYNTHESIS_INSTRUCTIONS_EN,
)


class TestBuildCategoryPrompt:
    def test_italian_contains_profile_and_category(self):
        result = build_category_prompt("Sono un CTO", "it", "Tech")
        assert SYSTEM_INSTRUCTION in result
        assert "Sono un CTO" in result
        assert "Tech" in result
        assert "implicazioni" in result  # Italian instructions

    def test_english_contains_profile_and_category(self):
        result = build_category_prompt("I'm a CTO", "en", "Tech")
        assert SYSTEM_INSTRUCTION in result
        assert "I'm a CTO" in result
        assert "Tech" in result
        assert "implications" in result  # English instructions

    def test_category_name_in_instructions(self):
        result = build_category_prompt("profile", "it", "Intelligenza Artificiale")
        assert "Intelligenza Artificiale" in result

    def test_unknown_language_defaults_to_italian(self):
        result = build_category_prompt("profile", "fr", "Tech")
        assert "implicazioni" in result

    def test_profile_delimiters(self):
        """Profile is wrapped in --- delimiters."""
        result = build_category_prompt("My profile text", "it", "Tech")
        assert "---\nMy profile text\n---" in result

    def test_empty_profile(self):
        result = build_category_prompt("", "it", "Tech")
        assert "---\n\n---" in result

    def test_multiline_profile(self):
        profile = "Line 1\nLine 2\nLine 3"
        result = build_category_prompt(profile, "it", "Tech")
        assert "Line 1\nLine 2\nLine 3" in result

    def test_special_chars_in_category(self):
        result = build_category_prompt("profile", "it", "AI & ML")
        assert "AI & ML" in result

    def test_system_instruction_always_first(self):
        result = build_category_prompt("profile", "it", "Tech")
        assert result.startswith(SYSTEM_INSTRUCTION)

    def test_italian_uses_it_instructions(self):
        result = build_category_prompt("p", "it", "Cat")
        assert "Scrivi in italiano" in result

    def test_english_uses_en_instructions(self):
        result = build_category_prompt("p", "en", "Cat")
        assert "Write in English" in result


class TestBuildSynthesisPrompt:
    def test_italian_contains_all_sections(self):
        result = build_synthesis_prompt("Sono un CTO", "it", "2026-04-05")
        assert SYSTEM_INSTRUCTION in result
        assert "Sono un CTO" in result
        assert "Da sapere oggi" in result
        assert "Richiede attenzione" in result
        assert "Da leggere con calma" in result
        assert "Spunti" in result
        assert "2026-04-05" in result

    def test_english_contains_all_sections(self):
        result = build_synthesis_prompt("I'm a CTO", "en", "2026-04-05")
        assert "Must know today" in result
        assert "Needs attention" in result
        assert "Deep reads" in result
        assert "Ideas" in result

    def test_profile_injected_verbatim(self):
        result = build_synthesis_prompt("Special chars: éàü", "it", "2026-04-05")
        assert "Special chars: éàü" in result

    def test_date_in_prompt(self):
        result = build_synthesis_prompt("p", "it", "2026-12-25")
        assert "2026-12-25" in result

    def test_unknown_language_defaults_to_italian(self):
        result = build_synthesis_prompt("p", "de", "2026-04-05")
        assert "Da sapere oggi" in result

    def test_profile_delimiters(self):
        result = build_synthesis_prompt("My profile", "en", "2026-04-05")
        assert "---\nMy profile\n---" in result

    def test_system_instruction_present(self):
        result = build_synthesis_prompt("p", "it", "2026-04-05")
        assert SYSTEM_INSTRUCTION in result

    def test_italian_no_repeat_instruction(self):
        result = build_synthesis_prompt("p", "it", "2026-04-05")
        assert "NON ripetere" in result

    def test_english_no_repeat_instruction(self):
        result = build_synthesis_prompt("p", "en", "2026-04-05")
        assert "do NOT repeat" in result


class TestBuildPromptLegacy:
    def test_still_works(self):
        result = build_prompt("profile", "it", ["Tech"], "2026-04-05")
        assert "Da sapere oggi" in result

    def test_defaults_to_italian(self):
        result = build_prompt("profile", "xx", ["Tech"], "2026-04-05")
        assert "Da sapere oggi" in result

    def test_delegates_to_synthesis_prompt(self):
        """build_prompt should produce same result as build_synthesis_prompt."""
        legacy = build_prompt("profile", "it", ["Tech", "Biz"], "2026-04-05")
        synthesis = build_synthesis_prompt("profile", "it", "2026-04-05")
        assert legacy == synthesis

    def test_categories_param_ignored(self):
        """Categories param doesn't affect output (it's for backward compat)."""
        r1 = build_prompt("p", "it", ["A"], "2026-04-05")
        r2 = build_prompt("p", "it", ["A", "B", "C"], "2026-04-05")
        assert r1 == r2


class TestConstantStrings:
    def test_system_instruction_not_empty(self):
        assert len(SYSTEM_INSTRUCTION) > 50

    def test_category_instructions_have_format_placeholder(self):
        assert "{category}" in CATEGORY_INSTRUCTIONS_IT
        assert "{category}" in CATEGORY_INSTRUCTIONS_EN

    def test_synthesis_instructions_have_sections(self):
        assert "## Da sapere oggi" in SYNTHESIS_INSTRUCTIONS_IT
        assert "## Must know today" in SYNTHESIS_INSTRUCTIONS_EN
