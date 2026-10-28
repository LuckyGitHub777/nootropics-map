#!/usr/bin/env python3
"""Lightweight static-site integrity and accessibility smoke checks."""
from __future__ import annotations
import json
import re
import shutil
import subprocess
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


HIGH_RISK_NAMES = ["cocaine", "fentanyl", "mdma", "adderall", "alprazolam", "epobis", "dihexa", "isrib", "semax", "modafinil", "phenibut"]

# Durable five-state search contract. Each case: query, expected state, expected strings, forbidden strings.
SEARCH_MATRIX = [
    ("Creatine", "reviewed", ["Reviewed record", "Creatine", "authoritative"], []),
    ("Weightlifting", "broader", ["Broader reviewed record", "Closest reviewed record: Physical activity", "broader than the searched term"],
     ["agree", "disagree", "confirm", "contradict"]),
    ("Caffeine", "published-2022", ["Published 2022 community source", "no reviewed Nootropics Map record", "self-reported", "not evidence of efficacy or safety"], []),
    ("Doing Math", "later-image", ["Later supplied image", "separate from the published 2022 analysis", "has not been published"],
     ["36,163", "2,802", "36163", "2802", "rating"]),
    ("Charlie Sheen", "not-mapped", ["Not mapped in this release", "not a complete inventory of the upstream dataset"],
     ["not in the source", "not in the 2022 dataset", "does not exist", "no evidence exists"]),
    # Normalization, partial matching and precedence.
    ("  cReAtInE  ", "reviewed", ["Creatine"], []),
    ("creat", "reviewed", ["Creatine"], []),
    ("WEIGHT", "broader", ["Physical activity"], []),
    ("caff", "published-2022", ["Caffeine"], []),
    ("math", "later-image", ["Doing Math"], []),
    ("meditation", "reviewed", ["Meditation"], []),
    ("exercise", "reviewed", ["Physical activity"], []),
    ("sleep", "reviewed", ["Sleep"], []),
    ("", "empty", [], []),
    ("   ", "empty", [], []),
    ("<img src=x onerror=alert(1)>", "not-mapped", ["“<img src=x onerror=alert(1)>”"], []),
]

HARNESS = r"""
const interventions = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
const out = cases.map((q) => {
  const result = resolveSearch(q, interventions);
  const view = describeResolution(result);
  return { q, state: result.state, view, actions: view ? view.actions.map((a) => a.slug) : [] };
});
console.log(JSON.stringify(out));
"""


def check_search_states(html: str, app_text: str, css: str) -> list[str]:
    errors: list[str] = []
    start, end = "// search-resolution:start", "// search-resolution:end"
    if start not in app_text or end not in app_text:
        return ["search-resolution block markers missing from app.js"]
    block = app_text[app_text.index(start):app_text.index(end)]

    # The resolver is navigation metadata: never a dataset, never quantitative, never innerHTML.
    if "innerHTML" in block:
        errors.append("search resolution must not build markup from strings")
    if re.search(r"\d{2,}[,.]\d|\b(count|ratings?|proba|p10|x:|y:)\s*:", block):
        errors.append("search context must not carry counts, probabilities or coordinates")
    entries = re.findall(r"\{ term: '", block)
    if not 4 <= len(entries) <= 12:
        errors.append(f"source context must stay a small curated map (found {len(entries)} terms)")
    if "fetch(" in block:
        errors.append("search resolution must not load an external or community dataset")

    # Markup and accessibility contract.
    for needle in ['id="searchResolution"', 'id="searchAnnounce" role="status" aria-live="polite"', 'aria-describedby="searchScope"']:
        if needle not in html:
            errors.append(f"search-resolution markup missing: {needle}")
    if not re.search(r'id="searchResolution"[^>]*\bhidden\b', html):
        errors.append("search-resolution panel must start hidden (quiet when the search is empty)")
    if "No matching evidence records." in html:
        errors.append("dead-end empty state returned")
    if "setTimeout" not in app_text or "lastAnnounced" not in app_text:
        errors.append("search status must be debounced and de-duplicated for screen readers")
    if not re.search(r"\.search-resolution\s*\{[^}]*text-align:\s*center", css):
        errors.append("search-resolution panel must stay centered")
    if "event.key === '/'" not in app_text:
        errors.append("keyboard / shortcut lost")

    public = (html + app_text).lower()
    for name in HIGH_RISK_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", public):
            errors.append(f"named high-risk substance on the evidence map: {name}")
    for raw in ["count_without_ssc", "proba_life_changing", "results_summary", ".csv"]:
        if raw in public:
            errors.append(f"raw community dataset reference on the evidence map: {raw}")

    node = shutil.which("node")
    if not node:
        return errors + ["node is required to run the search-state matrix"]
    interventions = (ROOT / "data" / "interventions.json").read_text(encoding="utf-8")
    run = subprocess.run([node, "-e", block + HARNESS, interventions, json.dumps([c[0] for c in SEARCH_MATRIX])],
                         capture_output=True, text=True, timeout=30)
    if run.returncode != 0:
        return errors + [f"search-state matrix could not run: {run.stderr.strip()[:300]}"]
    for (query, expected, must, mustnot), got in zip(SEARCH_MATRIX, json.loads(run.stdout)):
        if got["state"] != expected:
            errors.append(f"search {query!r}: expected {expected}, got {got['state']}")
            continue
        view = got["view"]
        if expected == "empty":
            if view is not None:
                errors.append("empty search must leave the current experience unchanged")
            continue
        copy = " ".join(str(view.get(k) or "") for k in ("label", "title", "body", "secondary"))
        for needle in must:
            if needle not in copy:
                errors.append(f"search {query!r}: missing wording {needle!r}")
        for needle in mustnot:
            if needle.lower() in copy.lower():
                errors.append(f"search {query!r}: forbidden wording {needle!r}")
        if expected in ("reviewed", "broader") and not got["actions"]:
            errors.append(f"search {query!r}: reviewed result needs an open-record action")
        if expected not in ("reviewed", "broader") and got["actions"]:
            errors.append(f"search {query!r}: source-only or unmapped terms must not offer a record action")
    by_query = {g["q"]: g for g in json.loads(run.stdout)}
    if by_query.get("Creatine", {}).get("actions") != ["creatine"]:
        errors.append("Creatine action must open the Creatine record")
    if by_query.get("Weightlifting", {}).get("actions") != ["physical-activity"]:
        errors.append("Weightlifting action must open the Physical activity record")
    return errors


# Readability floor: visible labels stay at about 11px (.68rem = 10.88px) or larger.
FLOOR_PX = 10.88
# The one deliberate exception: mobile map axis ticks are centred on the fixed y-axis gutter
# (test_map_geometry: "mobile y-axis gutter"); larger ticks cross the plot frame. Their words stay
# readable in the HTML map key and axis captions. The orbit centre caption ("published 2022") is
# likewise bounded by the centre circle's chord, so it stays at 12px in SVG units.
FLOOR_EXCEPTIONS = {("web/styles.css", ".axis-label", "10px")}
FLOOR_SELECTORS = [".mini-label", ".node-sublabel", ".band-badge", ".source-link small", ".source-claim-id",
                   ".map-key-item small", ".axis-label", ".axis-caption", ".hero-principles span", ".category-tag",
                   ".receipt-label", ".principle span", ".trust-pillars span", ".legend", ".resolution-label"]


def css_rules(path: Path):
    css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        yield m.group(1).strip().splitlines()[-1].strip(), m.group(2)


def check_readability_floor() -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for rel in ("web/styles.css", "web/explore.css"):
        for selector, body in css_rules(ROOT / rel):
            for decl in re.findall(r"font(?:-size)?\s*:\s*([^;]+)", body):
                for num, unit in re.findall(r"(\d*\.?\d+)(rem|px)\b", decl):
                    size = float(num) * (16 if unit == "rem" else 1)
                    if size < FLOOR_PX and (rel, selector, f"{num}{unit}") not in FLOOR_EXCEPTIONS:
                        errors.append(f"readability floor: {rel} {selector} uses {num}{unit} (< {FLOOR_PX}px)")
            seen.update(s.strip() for s in selector.split(","))
    for selector in FLOOR_SELECTORS:
        if selector not in seen:
            errors.append(f"readability floor: guarded selector {selector} not found")
    styles = (ROOT / "web/styles.css").read_text(encoding="utf-8")
    explore = (ROOT / "web/explore.css").read_text(encoding="utf-8")
    # SVG text scales with its viewBox; these rules keep it near 11px where each drawing shrinks.
    svg_rules = [
        (styles, r"@media \(min-width: 651px\) and \(max-width: 1199px\) \{[^@]*\.axis-label \{ font-size:13\.8px", "desktop map axis labels 13.8px (651–1199)"),
        (styles, r"@media \(min-width: 651px\) and \(max-width: 1199px\) \{[^@]*\.node-sublabel \{ font-size:14px", "desktop map sublabels 14px (651–1199)"),
        (styles, r"@media \(max-width: 650px\) \{ \.node-index \{ font-size:12\.5px", "mobile map indices 12.5px"),
        (explore, r"@media \(min-width: 980px\) and \(max-width: 1199px\) \{ \.o-num \{ font-size: 14\.5px", "orbit branch numbers 14.5px (980–1199)"),
        (explore, r"\.o-csub \{ font: 400 12px", "orbit centre caption 12px (largest size inside the centre circle)"),
    ]
    for source, pattern, label in svg_rules:
        if not re.search(pattern, source):
            errors.append(f"readability floor: missing SVG scaling rule for {label}")
    return errors


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

    errors.extend(check_search_states(text, app_text, css))
    errors.extend(check_readability_floor())

    if errors:
        print("SITE TEST: FAIL")
        for e in errors: print(f" - {e}")
        return 1
    print("SITE TEST: PASS — structural, dependency, and accessibility smoke checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
