"""HTML generation from markdown — shared building block for PDF and EPUB."""
from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")
_HR_RE = re.compile(r"^-{3,}$")

_THEMES: dict[str, dict[str, str]] = {
    "corporate": {
        "body_bg": "#ffffff",
        "body_color": "#374151",
        "h1_color": "#1a1a2e",
        "h2_color": "#16213e",
        "h3_color": "#0f3460",
        "accent": "#e94560",
        "link_color": "#2563eb",
        "strong_color": "#16213e",
        "border_color": "#d1d5db",
        "header_color": "#6b7280",
        "footer_color": "#6b7280",
    },
    "minimal": {
        "body_bg": "#fafaf9",
        "body_color": "#1a1a1a",
        "h1_color": "#1a1a1a",
        "h2_color": "#1a1a1a",
        "h3_color": "#1a1a1a",
        "accent": "#a3a3a3",
        "link_color": "#1e3a5f",
        "strong_color": "#1a1a1a",
        "border_color": "#d4d4d4",
        "header_color": "#737373",
        "footer_color": "#737373",
    },
    "dark": {
        "body_bg": "#1a1a2e",
        "body_color": "#e0e0e0",
        "h1_color": "#e0e0e0",
        "h2_color": "#c0c0d0",
        "h3_color": "#a0a0b8",
        "accent": "#e94560",
        "link_color": "#82b1ff",
        "strong_color": "#ffffff",
        "border_color": "#3a3a5e",
        "header_color": "#8888aa",
        "footer_color": "#8888aa",
    },
}

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
    color: {theme_body_color};
    background: {theme_body_bg};
    max-width: 680px;
    margin: 0 auto;
    padding: 2.5cm 1.5cm;
  }}

  /* Headings */
  h1 {{
    font-size: 22pt;
    font-weight: bold;
    color: {theme_h1_color};
    margin-top: 0;
    margin-bottom: 0.5em;
    padding-bottom: 0.25em;
    border-bottom: 3px solid {theme_accent};
  }}

  h2 {{
    font-size: 14pt;
    font-weight: bold;
    color: {theme_h2_color};
    margin-top: 1.4em;
    margin-bottom: 0.4em;
    padding-left: 0.6em;
    border-left: 4px solid {theme_accent};
  }}

  h3 {{
    font-size: 12pt;
    font-weight: bold;
    color: {theme_h3_color};
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
    color: {theme_strong_color};
  }}

  a {{
    color: {theme_link_color};
    text-decoration: underline;
  }}

  hr {{
    border: none;
    border-top: 1px solid {theme_border_color};
    margin: 1.5em 0;
  }}

  /* Header & footer */
  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 8pt;
    color: {theme_header_color};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid {theme_border_color};
    padding-bottom: 0.4em;
    margin-bottom: 1.5em;
  }}

  .page-header .brand {{
    font-weight: bold;
    color: {theme_accent};
  }}

  .page-footer {{
    font-size: 8pt;
    color: {theme_footer_color};
    text-align: center;
    border-top: 1px solid {theme_border_color};
    padding-top: 0.4em;
    margin-top: 2em;
  }}

  /* Print */
  @page {{
    size: A4;
    margin: 2.5cm;
  }}
  @media print {{
    body {{
      max-width: none;
      padding: 0;
      font-size: 10pt;
    }}

    h1 {{ font-size: 20pt; }}
    h2 {{ font-size: 13pt; }}
    h3 {{ font-size: 11pt; }}

    .page-header, .page-footer {{
      position: running(header);
    }}

    a {{
      color: {theme_h1_color};
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
    text = html_mod.escape(text, quote=False)
    text = _LINK_RE.sub(r'<a href="\2" target="_blank">\1</a>', text)
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
    theme: str = "corporate",
) -> str:
    """Generate a standalone HTML file from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.html"

    date_display = _display_date(date)
    body = markdown_to_html(markdown)

    theme_vars = _THEMES.get(theme, _THEMES["corporate"])

    html = _HTML_TEMPLATE.format(
        lang=language,
        date=date,
        date_display=date_display,
        body=body,
        theme_body_bg=theme_vars["body_bg"],
        theme_body_color=theme_vars["body_color"],
        theme_h1_color=theme_vars["h1_color"],
        theme_h2_color=theme_vars["h2_color"],
        theme_h3_color=theme_vars["h3_color"],
        theme_accent=theme_vars["accent"],
        theme_link_color=theme_vars["link_color"],
        theme_strong_color=theme_vars["strong_color"],
        theme_border_color=theme_vars["border_color"],
        theme_header_color=theme_vars["header_color"],
        theme_footer_color=theme_vars["footer_color"],
    )

    output_path.write_text(html, encoding="utf-8")
    return str(output_path)
