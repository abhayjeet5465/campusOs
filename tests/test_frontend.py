"""Catches the frontend failure that has no stack trace: JS reaching for an id the HTML
dropped during an edit. The handler silently does nothing and the button looks dead.
"""
import re, html.parser, pathlib, sys

FE = pathlib.Path(__file__).parent.parent / "frontend"


class Collector(html.parser.HTMLParser):
    VOID = {"meta", "link", "input", "br", "img", "hr", "source"}

    def __init__(self):
        super().__init__()
        self.ids, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.append(d["id"])
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()


def main():
    p = Collector()
    p.feed((FE / "index.html").read_text(encoding="utf-8"))
    js = (FE / "app.js").read_text(encoding="utf-8")

    referenced = set(re.findall(r"\$\('#([a-zA-Z0-9_-]+)'\)", js))
    missing = referenced - set(p.ids)
    assert not missing, f"app.js references ids absent from index.html: {sorted(missing)}"
    assert not p.stack, f"unclosed tags in index.html: {p.stack}"
    assert len(p.ids) == len(set(p.ids)), "duplicate id in index.html"

    # Accessibility floor: voice must never be the only input path (PRD §15).
    assert "keydown" in js and "mic" in js, "mic has no keyboard handler"
    assert 'aria-live' in (FE / "index.html").read_text(encoding="utf-8"), "no live region for status"

    print(f"frontend OK: {len(p.ids)} ids, {len(referenced)} referenced by JS, all present")


if __name__ == "__main__":
    main()
