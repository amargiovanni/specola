from src.prompt_builder import (
    build_category_prompt,
    build_synthesis_prompt,
    build_prompt,
    SYSTEM_INSTRUCTION,
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


class TestBuildPromptLegacy:
    def test_still_works(self):
        result = build_prompt("profile", "it", ["Tech"], "2026-04-05")
        assert "Da sapere oggi" in result

    def test_defaults_to_italian(self):
        result = build_prompt("profile", "xx", ["Tech"], "2026-04-05")
        assert "Da sapere oggi" in result
