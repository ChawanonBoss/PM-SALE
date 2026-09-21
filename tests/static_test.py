"""Static checks on index.html: no markup leaked out as visible text (a bad find/replace once printed `class="tab-panel" ...` on the dashboard),
and - when the `esprima` package is installed (pip install esprima) - every inline script parses."""
import os, re, sys
from html.parser import HTMLParser
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
SRC = open(PATH, encoding="utf-8").read()

class P(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.skip = 0; self.bad = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "textarea"): self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "textarea") and self.skip: self.skip -= 1
    def handle_data(self, data):
        s = data.strip()
        if self.skip or not s: return
        if re.search(r'\b[a-z-]+="[^"]*"', s) or s.startswith(">") or s.startswith("<"): self.bad.append((self.getpos()[0], s[:80]))
p = P(); p.feed(SRC)
assert not p.bad, ("markup shown as text", p.bad)
print("no stray markup text")
try:
    import esprima
    for i, code in enumerate(re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", SRC, re.S)): esprima.parseScript(code)
    print("inline scripts parse")
except ImportError:
    print("(esprima not installed: script syntax check skipped)")
print("OK")
