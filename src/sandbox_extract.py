"""Runs INSIDE the Daytona sandbox (stdlib only). Fetches a page from the local server and prints its text.

usage: python3 extract.py <path> [html_text|visible_text]
  html_text    : all text nodes, including hidden tab panels (like a crawler / BeautifulSoup get_text).
                 <style> and normal <script> are dropped; JSON-LD <script> blocks are kept.
  visible_text : same, but drops subtrees with the `hidden` attribute or inline display:none
                 (static approximation of what a browser shows; NOT a real browser render).
"""
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "li", "tr", "section", "header", "footer", "nav", "table", "ul", "br", "button"}


class Extract(HTMLParser):
    def __init__(self, visible_only):
        super().__init__()
        self.visible_only = visible_only
        self.stack = []  # (tag, skip)
        self.out = []

    def skipping(self):
        return any(s for _, s in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        skip = False
        if tag == "style" or (tag == "script" and a.get("type") != "application/ld+json"):
            skip = True
        if self.visible_only and ("hidden" in a or "display:none" in (a.get("style") or "").replace(" ", "")):
            skip = True
        if tag in BLOCK:
            self.out.append("\n")
        if tag in VOID:
            return
        self.stack.append((tag, skip))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in BLOCK:
            self.out.append("\n")
        elif tag == "td" or tag == "th":
            self.out.append(" | ")

    def handle_data(self, data):
        if not self.skipping() and data.strip():
            self.out.append(data.strip() + " ")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/"
    mode = sys.argv[2] if len(sys.argv) > 2 else "html_text"
    u = urllib.parse.urlparse(path)
    path = u.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    try:
        html = urllib.request.urlopen("http://localhost:8000" + path, timeout=10).read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: could not open {path}: {e}")
        return
    p = Extract(mode == "visible_text")
    p.feed(html)
    lines = [ln.strip() for ln in "".join(p.out).splitlines()]
    print("\n".join(ln for ln in lines if ln))


main()
