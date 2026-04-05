import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_opml_path():
    return FIXTURES_DIR / "sample.opml"


@pytest.fixture
def tmp_output_dir(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def sample_items_by_category():
    return {
        "Tech": [
            {
                "title": "OpenAI releases GPT-5",
                "link": "https://example.com/gpt5",
                "published": "2026-04-05 09:30",
                "summary": "OpenAI has announced GPT-5 with improved reasoning.",
                "source": "TechCrunch",
            },
            {
                "title": "EU AI Act enforcement begins",
                "link": "https://example.com/ai-act",
                "published": "2026-04-05 08:15",
                "summary": "The EU AI Act enters enforcement phase today.",
                "source": "The Verge",
            },
        ],
        "Business": [
            {
                "title": "ECB holds rates steady",
                "link": "https://example.com/ecb",
                "published": "2026-04-05 07:00",
                "summary": "The European Central Bank maintained interest rates.",
                "source": "Bloomberg",
            },
        ],
    }
