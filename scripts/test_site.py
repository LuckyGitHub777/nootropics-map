#!/usr/bin/env python3
"""Lightweight static-site integrity and accessibility smoke checks."""
from __future__ import annotations
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []
        self.styles = []
        self.lang = None
        self.inputs = []
        self.dialogs = []
        self.h1 = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html": self.lang = a.get("lang")
        if tag == "script" and a.get("src"): self.scripts.append(a["src"])
        if tag == "link" and a.get("rel") == "stylesheet": self.styles.append(a.get("href"))
        if tag == "input": self.inputs.append(a)
        if tag == "dialog": self.dialogs.append(a)
        if tag == "h1": self.h1 += 1


def local_ref_exists(ref: str) -> bool:
    if not ref or ref.startswith(("http://", "https://", "//", "#")):
        return True
    return (WEB / ref).resolve().exists()


def main() -> int:
    html_path = WEB / "index.html"
    text = html_path.read_text(encoding="utf-8")
    parser = Inspector(); parser.feed(text)
    errors = []
    required_ids = {"searchInput", "evidenceMap", "cardGrid", "detailDialog", "trustDialog", "methodDialog", "reviewDate", "mapKey", "mapStatus", "methodButton", "trustButton"}
    missing = required_ids - parser.ids
    if missing: errors.append(f"missing required IDs: {sorted(missing)}")
    if parser.lang != "en": errors.append("html lang must be en")
    if parser.h1 != 1: errors.append(f"expected exactly one h1, found {parser.h1}")
    for ref in parser.scripts + parser.styles:
        if ref.startswith(("http://", "https://", "//")):
            errors.append(f"external runtime dependency not allowed in v0.1: {ref}")
        elif not local_ref_exists(ref):
            errors.append(f"missing local asset: {ref}")
    if "prefers-reduced-motion" not in (WEB / "styles.css").read_text(encoding="utf-8"):
        errors.append("reduced-motion support missing")
    if "aria-live" not in text:
        errors.append("dynamic evidence grid should expose aria-live")
    if 'id="mapStatus" role="status" aria-live="polite"' not in text:
        errors.append("map result status should be politely announced")
    if text.count('aria-pressed="') < 7:
        errors.append("filter/detail toggles should expose aria-pressed state")
    canonical = 'https://luckygithub777.github.io/nootropics-map/'
    if f'rel="canonical" href="{canonical}"' not in text:
        errors.append("canonical Pages URL missing")
    if f'property="og:url" content="{canonical}"' not in text:
        errors.append("Open Graph URL missing")
    if 'social-preview.png' not in text or not (WEB / "social-preview.png").exists():
        errors.append("first-party social preview missing")
    app_text = (WEB / "app.js").read_text(encoding="utf-8")
    for token in ("history.pushState", "syncDetailFromLocation", "popstate", "hashchange"):
        if token not in app_text:
            errors.append(f"deep-link contract missing: {token}")
    if ".ghost-button { display:none; }" in (WEB / "styles.css").read_text(encoding="utf-8"):
        errors.append("mobile Method control must remain available")
    if not parser.dialogs:
        errors.append("detail dialogs missing")
    if not (WEB / "favicon.svg").exists():
        errors.append("favicon missing")

    # Centered spine: Explore, Evidence Library and Trust Architecture stay on one centered axis.
    css = (WEB / "styles.css").read_text(encoding="utf-8")
    marker = "/* Centered spine:"
    if marker not in css:
        errors.append("centered-spine stylesheet block missing")
    else:
        spine = css[css.index(marker):]
        required = {
            ".section-heading": ["align-items:center", "text-align:center"],
            ".section-note": ["text-align:center"],
            ".filter-row": ["justify-content:center"],
            ".trust-strip": ["grid-template-columns:minmax(0,1fr)", "justify-items:center", "text-align:center"],
            ".trust-pillars > div": ["text-align:center"],
        }
        for selector, declarations in required.items():
            rule = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", spine)
            body = rule.group(1).replace(" ", "") if rule else ""
            for declaration in declarations:
                if declaration not in body:
                    errors.append(f"centered spine lost: {selector} needs {declaration}")
        if ".section-heading > div:not(.view-toggle)" not in spine or re.search(r"\.section-heading\s*>\s*div\s*\{", spine):
            errors.append("centered heading rule must not restyle the Simple/Detailed toggle")
        if not re.search(r"\.card-grid\s*\{[^}]*justify-content:\s*center", spine):
            errors.append("evidence card rows must wrap toward the center")
        if re.search(r"text-align\s*:\s*(left|start)|align-items\s*:\s*flex-start", spine):
            errors.append("centered spine overridden by a later left-aligned rule")

    if errors:
        print("SITE TEST: FAIL")
        for e in errors: print(f" - {e}")
        return 1
    print("SITE TEST: PASS — structural, dependency, and accessibility smoke checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
