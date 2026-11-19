"""A small HTML-to-text converter that keeps the structure the parsers need.

The league's injury-report hub and its weekly inactive-list article are
client-rendered pages. Their *rendered* content is in the document as ordinary
HTML, so a line-oriented view of that HTML is enough to read them.

Two things are preserved because the parsers depend on them:

* block elements start a new line, so headings and list items stay separate;
* links become ``[text](href)``, so the official game-centre URL that the
  inactive-list article prints next to each game is recoverable.
"""

from __future__ import annotations

import html as html_module
import re
from html.parser import HTMLParser

BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "div", "dl", "dd", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
    "h5", "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section",
    "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._skip = 0

    # -- helpers ---------------------------------------------------------
    def _flush_link(self) -> None:
        if self._href is not None:
            text = re.sub(r"\s+", " ", "".join(self._link_text)).strip()
            self.chunks.append(f"[{text}]({self._href})")
            self._href = None
            self._link_text = []

    def _newline(self) -> None:
        self.chunks.append("\n")

    # -- parser hooks ----------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1
            return
        if self._skip:
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
        if tag in BLOCK_TAGS:
            self._newline()

    def handle_data(self, data):
        if self._skip:
            return
        if self._href is not None:
            self._link_text.append(data)
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
