"""A small HTML-to-text converter that keeps the structure the parsers need.

The league's injury-report hub and its weekly inactive-list article are
client-rendered pages. Their *rendered* content is in the document as ordinary
HTML, so a line-oriented view of that HTML is enough to read them.

Three things are preserved because the parsers depend on them:

* block elements start a new line, so headings and list items stay separate;
* links become ``[text](href)``, so the official game-centre URL that the
  inactive-list article prints next to each game is recoverable;
* a table row stays one line and keeps its **column positions**, so a row
  whose injury cell is empty is not silently shifted one column to the left.

A table row is written as ``| cell | cell | ... |``. The cells are separated
by a pipe and an empty cell is preserved as an empty cell, because the
league's injury table has five columns of which the injury and the game
status are often empty.
"""

from __future__ import annotations

import html as html_module
import re
from html.parser import HTMLParser

BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "div", "dl", "dd", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
    "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section",
    "table", "tbody", "tfoot", "thead", "ul",
}

CELL_TAGS = {"td", "th"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._skip = 0
        self._row_cells: list[str] | None = None
        self._cell_text: list[str] | None = None

    # -- helpers ---------------------------------------------------------
    def _flush_link(self) -> None:
        if self._href is not None:
            text = re.sub(r"\s+", " ", "".join(self._link_text)).strip()
            target = self._cell_text if self._cell_text is not None else self.chunks
            target.append(f"[{text}]({self._href})")
            self._href = None
            self._link_text = []

    def _newline(self) -> None:
        self.chunks.append("\n")

    # -- table handling --------------------------------------------------
    def _open_cell(self) -> None:
        self._flush_link()
        self._cell_text = []

    def _close_cell(self) -> None:
        self._flush_link()
        if self._row_cells is None:
            self._row_cells = []
        if self._cell_text is None:
            self._cell_text = []
        text = re.sub(r"\s+", " ", "".join(self._cell_text)).strip()
        self._row_cells.append(text)
        self._cell_text = None

    def _close_row(self) -> None:
        self._flush_link()
        if self._row_cells is not None:
            self.chunks.append("\n")
            self.chunks.append("| " + " | ".join(self._row_cells) + " |")
            self.chunks.append("\n")
        self._row_cells = None
        self._cell_text = None

    # -- parser hooks ----------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1
            return
        if self._skip:
            return
        if tag == "tr":
            self._newline()
            self._row_cells = []
            self._cell_text = None
            return
        if tag in CELL_TAGS:
            self._open_cell()
            return
        if tag in BLOCK_TAGS:
            self._newline()
        if tag == "a":
            self._flush_link()
            self._href = dict(attrs).get("href", "")
            self._link_text = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag == "a":
            self._flush_link()
        if tag in CELL_TAGS:
            self._close_cell()
            return
        if tag == "tr":
            self._close_row()
            return
        if tag in BLOCK_TAGS:
            self._newline()

    def handle_data(self, data):
        if self._skip:
            return
        if self._href is not None:
            # Text inside a link belongs to the link, whether or not the link
            # sits inside a table cell.
            self._link_text.append(data)
        elif self._cell_text is not None:
            self._cell_text.append(data)
        else:
            self.chunks.append(data)

    def close(self):  # noqa: D102 - inherited behaviour
        super().close()
        self._flush_link()


def html_to_lines(html: str) -> list[str]:
    """Return the document as a list of non-empty, whitespace-collapsed lines."""
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return []
    text = html_module.unescape("".join(parser.chunks))
    lines = []
    for raw in text.split("\n"):
        line = re.sub(r"[ \t\r\f\v]+", " ", raw).strip()
        if line:
            lines.append(line)
    return lines


def split_table_row(line: str) -> list[str]:
    """Split a table row into its cells, keeping empty cells in place."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]
