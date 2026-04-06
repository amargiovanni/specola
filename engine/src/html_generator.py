"""HTML generation from markdown — shared building block for PDF and EPUB."""
from __future__ import annotations

import re
from pathlib import Path

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")
_HR_RE = re.compile(r"^-{3,}$")

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Specola — {date_display}</title>
<style>
  /* Reset & base */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #374151;
    background: #ffffff;
    max-width: 680px;
    margin: 0 auto;
    padding: 2.5cm 1.5cm;
  }}

  /* Headings */
  h1 {{
    font-size: 22pt;
    font-weight: bold;
    color: #1a1a2e;
    margin-top: 0;
    margin-bottom: 0.5em;
    padding-bottom: 0.25em;
    border-bottom: 3px solid #e94560;
  }}

  h2 {{
    font-size: 14pt;
    font-weight: bold;
    color: #16213e;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
    padding-left: 0.6em;
    border-left: 4px solid #e94560;
  }}

  h3 {{
    font-size: 12pt;
    font-weight: bold;
    color: #0f3460;
    margin-top: 1em;
    margin-bottom: 0.3em;
  }}

  /* Paragraphs & lists */
  p {{
    margin-bottom: 0.6em;
  }}

  ul, ol {{
    margin: 0.4em 0 0.6em 1.5em;
    padding: 0;
  }}

  li {{
    margin-bottom: 0.3em;
  }}

  /* Inline */
  strong {{
    color: #16213e;
  }}

  a {{
    color: #2563eb;
    text-decoration: underline;
  }}

  hr {{
    border: none;
    border-top: 1px solid #d1d5db;
    margin: 1.5em 0;
  }}

  /* Header & footer */
  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 8pt;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #d1d5db;
    padding-bottom: 0.4em;
    margin-bottom: 1.5em;
  }}

  .page-header .brand {{
    font-weight: bold;
    color: #e94560;
  }}

  .page-footer {{
    font-size: 8pt;
    color: #6b7280;
    text-align: center;
    border-top: 1px solid #d1d5db;
    padding-top: 0.4em;
    margin-top: 2em;
  }}

  /* Print */
  @media print {{
    body {{
      max-width: none;
      padding: 2.5cm;
      font-size: 10pt;
    }}

    h1 {{ font-size: 20pt; }}
    h2 {{ font-size: 13pt; }}
    h3 {{ font-size: 11pt; }}

    .page-header, .page-footer {{
      position: running(header);
    }}

    a {{
      color: #1a1a2e;
      text-decoration: none;
    }}

    h2, h3 {{
      page-break-after: avoid;
    }}
  }}
</style>
</head>
<body>
<div class="page-header">
  <span class="brand">Specola</span>
  <span>{date_display}</span>
</div>

{body}

<div class="page-footer">Specola &mdash; {date_display}</div>
</body>
</html>"""


def _inline_format(text: str) -> str:
    """Convert bold and link markdown to HTML inline elements."""
    # Links first, then bold (to avoid double-processing)
    text = _LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    return text


def markdown_to_html(markdown: str) -> str:
    """Convert briefing markdown to an HTML fragment (no <html>/<body> wrapper)."""
    lines = markdown.split("\n")
    parts: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            parts.append("</ul>")
            in_ul = False
        if in_ol:
            parts.append("</ol>")
            in_ol = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            close_lists()
            continue

        if _HR_RE.match(stripped):
            close_lists()
            parts.append("<hr>")
        elif stripped.startswith("### "):
            close_lists()
            parts.append(f"<h3>{_inline_format(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            close_lists()
            parts.append(f"<h2>{_inline_format(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            close_lists()
            parts.append(f"<h1>{_inline_format(stripped[2:])}</h1>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if in_ol:
                parts.append("</ol>")
                in_ol = False
            if not in_ul:
                parts.append("<ul>")
                in_ul = True
            parts.append(f"<li>{_inline_format(stripped[2:])}</li>")
        elif _NUMBERED_RE.match(stripped):
            if in_ul:
                parts.append("</ul>")
                in_ul = False
            if not in_ol:
                parts.append("<ol>")
                in_ol = True
            text = _NUMBERED_RE.sub("", stripped)
            parts.append(f"<li>{_inline_format(text)}</li>")
        else:
            close_lists()
            parts.append(f"<p>{_inline_format(stripped)}</p>")

    close_lists()
    return "\n".join(parts)


def _display_date(date: str) -> str:
    """Extract display date from timestamp. '2026-04-05_1930' -> '2026-04-05'."""
    return date.split("_")[0] if "_" in date else date


def generate_html(
    markdown: str,
    date: str,
    output_dir: str | Path,
    language: str = "it",
) -> str:
    """Generate a standalone HTML file from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.html"

    date_display = _display_date(date)
    body = markdown_to_html(markdown)

    html = _HTML_TEMPLATE.format(
        lang=language,
        date=date,
        date_display=date_display,
        body=body,
    )

    output_path.write_text(html, encoding="utf-8")
    return str(output_path)
