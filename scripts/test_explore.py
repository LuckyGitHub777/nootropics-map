#!/usr/bin/env python3
"""Structural, data-sourcing, and safety-boundary checks for the guided-reading page."""
from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
CANONICAL = "https://luckygithub777.github.io/nootropics-map/explore.html"
REQUIRED_IDS = {"paths", "pathOut", "orbit", "branchList", "readNext", "readPrev", "readCount",
                "readNodeTitle", "receiptGrid", "claimCount", "sourceCount", "reading", "receipts"}
# The community-signal layer stays out of the product until it has a provenance-complete dataset
# (docs/evidence-model.md). These markers would indicate signal placements or named high-risk items.
SIGNAL_GATE = ["uncommon-often", "wide-often", "wide-rarely", "uncommon-rarely", "quadrant"]
HIGH_RISK_NAMES = ["cocaine", "fentanyl", "mdma", "adderall", "alprazolam", "epobis", "dihexa", "isrib", "semax"]


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.h1 = 0
        self.lang = None
        self.scripts: list[str] = []
        self.styles: list[str] = []
        self.live: set[str] = set()
        self.blank_links_unsafe = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
            if a.get("aria-live"):
                self.live.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "link" and a.get("rel") == "stylesheet":
            self.styles.append(a.get("href", ""))
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
            self.blank_links_unsafe += 1


def main() -> int:
    errors: list[str] = []
    html = (WEB / "explore.html").read_text(encoding="utf-8")
    css = (WEB / "explore.css").read_text(encoding="utf-8")
    js = (WEB / "explore.js").read_text(encoding="utf-8")
    index = (WEB / "index.html").read_text(encoding="utf-8")
    base_css = (WEB / "styles.css").read_text(encoding="utf-8")

    p = Inspector(); p.feed(html)
    if p.lang != "en": errors.append("html lang must be en")
    if p.h1 != 1: errors.append(f"expected exactly one h1, found {p.h1}")
    missing = REQUIRED_IDS - p.ids
    if missing: errors.append(f"missing required IDs: {sorted(missing)}")
    if not {"pathOut", "receiptGrid"} <= p.live: errors.append("dynamic evidence regions must use aria-live")
    if 'class="skip-link"' not in html: errors.append("skip link missing")
    if p.blank_links_unsafe: errors.append("target=_blank links must use rel=noopener")
    for ref in p.scripts + p.styles:
        if ref.startswith(("http://", "https://", "//")):
            errors.append(f"external runtime dependency not allowed: {ref}")
        elif not (WEB / ref).resolve().exists():
            errors.append(f"missing local asset: {ref}")
    if f'rel="canonical" href="{CANONICAL}"' not in html: errors.append("canonical guided-reading URL missing")
    if "Safety boundary" not in html or "talk to a clinician" not in html: errors.append("safety boundary copy missing")
    if 'href="./explore.html"' not in index: errors.append("evidence map must link to the guided reading")

    if "prefers-reduced-motion" not in css: errors.append("reduced-motion support missing")
    for token in ["--bg", "--panel", "--text", "--muted", "--faint", "--accent"]:
        base = re.search(rf"{token}:\s*([^;]+);", base_css)
        mine = re.search(rf"{token}:\s*([^;]+);", css)
        if not base or not mine or base.group(1).strip() != mine.group(1).strip():
            errors.append(f"palette token {token} must match styles.css")

    fetches = set(re.findall(r"fetch\('([^']+)'\)", js))
    expected = {"../data/interventions.json", "../data/claims.json", "../data/sources.json"}
    if fetches != expected: errors.append(f"unexpected data fetches: {sorted(fetches)}")
    if "innerHTML" in js: errors.append("explore.js must not write innerHTML")

    claims = json.loads((ROOT / "data" / "claims.json").read_text(encoding="utf-8"))
    for claim in claims:
        if f"'{claim['id']}'" not in js:
            errors.append(f"pathway missing for {claim['id']}")

    reading = js[js.index("const READING"):js.index("const NODES")]
    branches = len(re.findall(r"\{ id: '", reading)) - 1
    leaves = len(re.findall(r"^\s+\['", reading, flags=re.M))
    if branches != 8 or 1 + branches + leaves != 47:
        errors.append(f"guided reading must have 8 branches and 47 ideas (found {branches} branches, {1 + branches + leaves} ideas)")

    public_text = (html + js).lower()
    for marker in SIGNAL_GATE:
        if marker in public_text: errors.append(f"community-signal placement leaked into the public page: {marker}")
    for name in HIGH_RISK_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", public_text): errors.append(f"named high-risk substance on public page: {name}")

    if errors:
        print("GUIDED READING TEST: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1
    print("GUIDED READING TEST: PASS — structure, data sourcing, 47-idea reading, and safety boundary verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
