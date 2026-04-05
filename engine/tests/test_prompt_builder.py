from src.prompt_builder import build_prompt, SYSTEM_INSTRUCTION, OUTPUT_INSTRUCTIONS_IT, OUTPUT_INSTRUCTIONS_EN


class TestBuildPrompt:
    def test_italian_prompt_contains_all_parts(self):
        profile = "Sono un CTO di una startup fintech."
        categories = ["Tech", "Business"]
        result = build_prompt(profile, "it", categories, "2026-04-05")
        assert SYSTEM_INSTRUCTION in result
        assert profile in result
        assert "Da sapere oggi" in result
        assert "Richiede attenzione" in result
        assert "Per area tematica" in result
        assert "Da leggere con calma" in result
        assert "Spunti" in result
        assert "Tech" in result
        assert "Business" in result

    def test_english_prompt_contains_all_parts(self):
        profile = "I'm a CTO at a fintech startup."
        categories = ["Tech"]
        result = build_prompt(profile, "en", categories, "2026-04-05")
        assert SYSTEM_INSTRUCTION in result
        assert profile in result
        assert "Must know today" in result
        assert "Needs attention" in result
        assert "By topic" in result
        assert "Deep reads" in result
        assert "Ideas" in result

    def test_profile_injected_verbatim(self):
        profile = "Custom profile with special chars: éàü"
        result = build_prompt(profile, "it", ["Tech"], "2026-04-05")
        assert "Custom profile with special chars: éàü" in result

    def test_date_included(self):
        result = build_prompt("profile", "it", ["Tech"], "2026-04-05")
        assert "2026-04-05" in result

    def test_categories_listed(self):
        categories = ["Tech", "Business", "Dev Tools"]
        result = build_prompt("profile", "it", categories, "2026-04-05")
        assert "Tech" in result
        assert "Business" in result
        assert "Dev Tools" in result

    def test_defaults_to_italian(self):
        result = build_prompt("profile", "xx", ["Tech"], "2026-04-05")
        assert "Da sapere oggi" in result
