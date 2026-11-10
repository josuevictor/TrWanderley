#!/usr/bin/env python3
"""
Gera docs/TUTORIAL_FINANCEIRO.pdf a partir de docs/TUTORIAL_FINANCEIRO.md

Dependências (requisito): fpdf2, markdown, fonte DejaVu no sistema (Ubuntu: fonts-dejavu-core).

Uso:
  python scripts/build_tutorial_financeiro_pdf.py
"""
from __future__ import annotations

import re
import sys
from html import unescape
from pathlib import Path

import markdown
from fpdf import FPDF
from fpdf.fonts import FontFace, TextStyle
from fpdf.html import DEFAULT_TAG_STYLES

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "TUTORIAL_FINANCEIRO.md"
OUT_PATH = ROOT / "docs" / "TUTORIAL_FINANCEIRO.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"


def _flatten_table_cell_innards(html: str) -> str:
    """
    fpdf2 HTML does not support nested tags inside <td>/<th> (e.g. <strong>).
    Markdown tables emit inline markup; strip inner tags and keep plain text.
    """

    def repl(match: re.Match[str]) -> str:
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        text = unescape(re.sub(r"<[^>]+>", "", inner))
        text = " ".join(text.split())
        return f"<{tag}{attrs}>{text}</{tag}>"

    return re.sub(
        r"<(td|th)((?:\s[^>]*)?)>(.*?)</\1>",
        repl,
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )


def build() -> None:
    if not FONT_REGULAR.exists():
        print("Fonte DejaVu não encontrada em", FONT_REGULAR, file=sys.stderr)
        print("No Ubuntu/Debian: sudo apt install fonts-dejavu-core", file=sys.stderr)
        sys.exit(1)
    if not MD_PATH.is_file():
        print("Ficheiro não encontrado:", MD_PATH, file=sys.stderr)
        sys.exit(1)

    md_text = MD_PATH.read_text(encoding="utf-8")
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "nl2br", "sane_lists"],
        extension_configs={"tables": {}},
    )
    body_html = _flatten_table_cell_innards(body_html)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/></head><body>
{body_html}
</body></html>"""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("DejaVu", "", str(FONT_REGULAR))
    pdf.add_font("DejaVu", "B", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR))
    # fonts-dejavu-core ships no true italic for DejaVu Sans; map I/BI so HTML <em> works.
    pdf.add_font("DejaVu", "I", str(FONT_REGULAR))
    pdf.add_font("DejaVu", "BI", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR))

    tag_styles = {}
    for tag, style in DEFAULT_TAG_STYLES.items():
        # TextStyle subclasses FontFace; check TextStyle first so replace() gets font_family=.
        if isinstance(style, TextStyle):
            tag_styles[tag] = style.replace(font_family="DejaVu")
        elif isinstance(style, FontFace):
            tag_styles[tag] = style.replace(family="DejaVu")

    # HTML2FPDF defaults to core font "times" for list bullets unless font_family matches a TTF.
    pdf.write_html(
        html,
        table_line_separators=True,
        tag_styles=tag_styles,
        font_family="DejaVu",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print("Gerado:", OUT_PATH)


if __name__ == "__main__":
    build()
