from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

root = Path('docs/sf-rent')
class Check(HTMLParser):
    def __init__(self):
        super().__init__(); self.row = False; self.link = False; self.errors = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tr': self.row, self.link = True, False
        if tag == 'a':
            h = a.get('href', '')
            if self.row and urlparse(h).scheme == 'https': self.link = True
            if h and not urlparse(h).scheme and not (root / h).exists(): self.errors.append('missing: ' + h)
        if tag == 'link' and not (root / a.get('href', '')).exists(): self.errors.append('missing stylesheet')
    def handle_endtag(self, tag):
        if tag == 'tr':
            # Header row has no source.
            if self.row and not self.link and getattr(self, 'seen_header', False): self.errors.append('unsourced row')
            self.seen_header = True; self.row = False
errors = []
for f in root.glob('*.html'):
    parser = Check(); parser.feed(f.read_text()); errors += [f'{f}: {e}' for e in parser.errors]
assert len(list(root.glob('*.html'))) == 5
assert not errors, errors
print('SF rent: 5 pages, all data rows source-linked, local links resolve')
