#!/usr/bin/env python3
"""The former guided-reading URL is a compatibility route into the single main page, not a second experience."""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
CANONICAL = "https://luckygithub777.github.io/nootropics-map/"
# Old guided-reading anchors and the main-page sections that replace them.
MOVED = {"sourceState": "map", "dataAboutData": "insights", "lenses": "evidence", "pathways": "evidence",
         "receipts": "evidence", "reading": "insights"}


def main() -> int:
    errors: list[str] = []
    html = (WEB / "explore.html").read_text(encoding="utf-8")
    js = (WEB / "explore.js").read_text(encoding="utf-8")
    index = (WEB / "index.html").read_text(encoding="utf-8")

    if f'rel="canonical" href="{CANONICAL}"' not in html:
        errors.append("compatibility route must declare the main page as canonical")
    if 'name="robots" content="noindex,follow"' not in html:
        errors.append("compatibility route must not be indexed as its own page")
    if '<script src="./explore.js"></script>' not in html:
        errors.append("compatibility route must load its redirect script")
    if not re.search(r'<noscript><meta http-equiv="refresh" content="0; url=\./" /></noscript>', html):
        errors.append("no-script redirect fallback missing")
    if 'id="continue" href="./"' not in html:
        errors.append("visible fallback link to the main page missing")
    if re.search(r"<(section|h1|h2|dialog|svg|table)\b", html) or len(re.sub(r"<[^>]+>|\s+", " ", html.split("<body>")[1]).split()) > 20:
        errors.append("compatibility route must not carry a second experience")

    found = dict(re.findall(r"(\w+): '(\w+)'", js[js.index("const MOVED"):js.index("};")]))
    if found != MOVED:
        errors.append(f"anchor mapping drifted: {found}")
    for target in set(MOVED.values()):
        if f'id="{target}"' not in index:
            errors.append(f"mapped section #{target} missing from the main page")
    if "window.location.replace(" not in js:
        errors.append("redirect must replace the history entry")
    if "fetch(" in js or "innerHTML" in js:
        errors.append("compatibility script must not load data or write markup")
    if (WEB / "explore.css").exists():
        errors.append("retired guided-reading stylesheet is still published")

    if errors:
        print("COMPATIBILITY ROUTE TEST: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1
    print("COMPATIBILITY ROUTE TEST: PASS — explore.html redirects old anchors into the single main page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
