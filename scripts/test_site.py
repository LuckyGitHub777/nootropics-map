#!/usr/bin/env python3
"""Structure, copy, data-fidelity, search and readability checks for the single public page."""
from __future__ import annotations
import html as html_lib
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
CANONICAL = "https://luckygithub777.github.io/nootropics-map/"
SECTION_ORDER = ["map", "insights", "snapshots", "data", "evidence", "sources"]
NAV = [("#map", "Map"), ("#insights", "Insights"), ("#evidence", "Evidence"), ("#sources", "Sources")]
REQUIRED_IDS = {"communityMap", "mapKey", "mapKeyBody", "searchInput", "searchResolution", "searchAnnounce", "evidenceList",
                "emptyState", "detailDialog", "dialogContent", "reviewedSources", "reviewNote", *SECTION_ORDER}
HIGH_RISK_NAMES = ["cocaine", "fentanyl", "mdma", "adderall", "alprazolam", "epobis", "dihexa", "isrib", "semax", "modafinil", "phenibut"]
SAFETY_LINE = "Information only. Not medical advice. No diagnosis, treatment, dosing, or personal recommendations."
# Visitor-facing copy explains the subject, not the product, and does not address the reader.
BANNED_PHRASES = ["system of record", "git", "pull request", "required check", "ci ", "build", "versioned", "versionable",
                  "north star", "trust architecture", "why trust", "trust the trace", "front door", "v0.", "in this release",
                  "guided reading", "talk to a clinician", "clinician", "receipt", "pathway",
                  # Undefined scale jargon and over-broad provenance claims.
                  "chance of a 10", "of a 10", "rarely a 10", "often a 10", "every number on this page"]
# Zero-context rule: no visitor-facing string may assume another image is visible, or describe how the site,
# its sources or its search machinery came to be. Checked across visible text, screen-reader text, attributes,
# share metadata, generated search copy and the compatibility page.
CONTEXT_LEAKS = ["the chart changed", "two snapshots", "about the two snapshots", "doing math appears",
                 "doing math changes how the chart reads", "later supplied image", "supplied", "source state",
                 "published state", "snapshot", "current index", "current release", "upstream dataset", "upstream",
                 "visibly different places", "undocumented", "neither version", "has moved", "no reviewed record yet",
                 "new ratings"]
CONTEXT_REQUIRED = ["Published data vs. later image", "Published 2022 data", "underlying data is unavailable"]
SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself)\b", re.I)

# Published 2022 community analysis: the seven cited values (result table, verified 2026-10-28 against
# results_summary.csv in the published analysis repository). Not a dataset; a small attributed citation set.
CITED = {
    "Weightlifting": (567, 0.121, 0.093, 0.153),
    "Trying to get more sleep": (993, 0.075, 0.060, 0.093),
    "Meditation": (429, 0.066, 0.046, 0.093),
    "Caffeine": (2553, 0.030, 0.025, 0.037),
    "Creatine": (1153, 0.014, 0.010, 0.020),
    "Theanine": (1322, 0.013, 0.009, 0.018),
    "Omega-3": (956, 0.010, 0.006, 0.014),
}
# Facts stated in the insights, each derived from the citation set or the published plotting code.
INSIGHT_FACTS = ["top ten of 125 items", "Weightlifting ranks third", "Third of 125 items at 0.121", "2,553 ratings",
                 "more than any other item", "0.030", "956 to 1,322 ratings", "ρ ≈ 0.14", "fewer than 50 ratings", "about four times wider",
                 "500 or more", "Doing Math", "absent from the published 2022 dataset"]
DATA_FACTS = ["125", "116", "125 result-table items · 116 plotted", "ρ ≈ 0.14", "Popularity barely tracks reported transformation.",
              "≈4×", "≈0.048", "≈0.012", "≈3.9×", "Sparse estimates are much less precise.", "20 items in each group",
              "More ratings improve precision. They do not turn self-report into an experiment."]


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.scripts: list[str] = []
        self.styles: list[str] = []
        self.lang = None
        self.h1 = 0
        self.nav: list[tuple[str, str]] = []
        self._in_nav = False
        self._href = None
        self.visible: list[str] = []
        self._skip = 0
        self._sr = 0
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "link" and a.get("rel") == "stylesheet":
            self.styles.append(a.get("href", ""))
        if tag == "nav":
            self._in_nav = True
        if self._in_nav and tag == "a":
            self._href = a.get("href")
        if tag in ("script", "style", "head", "title", "svg", "dialog"):
            self._skip += 1
        if "sr-only" in (a.get("class") or "").split():
            self._sr += 1
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if tag in ("script", "style", "head", "title", "svg", "dialog"):
            self._skip -= 1
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
            self._sr -= 1

    def handle_data(self, data):
        if self._in_nav and self._href and data.strip():
            self.nav.append((self._href, data.strip()))
            self._href = None
        if not self._skip and not self._sr and data.strip():
            self.visible.append(data.strip())


def js_user_strings(app: str) -> str:
    """Quoted strings in app.js that can reach the page (excludes selectors, ids and code-only tokens)."""
    strings = re.findall(r"'([^'\\\n]{4,})'|`([^`]{4,})`", app)
    out = [a or b for a, b in strings]
    return " ".join(s for s in out if " " in s and not s.startswith(("#", ".", "http", "(max-width", "translate(")))


HARNESS = r"""
const interventions = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map((q) => {
  const result = resolveSearch(q, interventions);
  const view = describeResolution(result);
  return { q, state: result.state, view, actions: view ? view.actions.map((a) => a.slug) : [] };
})));
"""

# Durable five-state search contract: query, state, required wording, forbidden wording.
SEARCH_MATRIX = [
    ("Creatine", "reviewed", ["Reviewed", "Creatine", "claim, limitations and sources", "Different questions."], []),
    ("Weightlifting", "broader", ["Related evidence", "Physical activity", "broader than the searched term"], ["agree", "confirm", "contradict"]),
    ("Caffeine", "published-2022", ["2022 chart", "published 2022 community analysis", "no reviewed record", "not evidence of efficacy or safety"], ["yet"]),
    ("Omega-3", "published-2022", ["2022 chart", "Omega-3"], []),
    ("Doing Math", "later-image", ["Later image", "Doing Math appears in a separate later image but not in the published 2022 dataset.",
                                   "underlying data is unavailable, so no numerical comparison is made"],
     ["36,163", "2,802", "rating", "0.", "rank", "probability", "supplied", "undocumented", "snapshot"]),
    ("Charlie Sheen", "not-mapped", ["No matching entry", "Search includes the reviewed evidence and selected chart labels shown on this page."],
     ["not in the source", "does not exist", "no evidence exists", "release", "index", "upstream", "dataset"]),
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


def check_search(html: str, app: str) -> list[str]:
    errors: list[str] = []
    start, end = "// search-resolution:start", "// search-resolution:end"
    if start not in app or end not in app:
        return ["search-resolution block markers missing from app.js"]
    block = app[app.index(start):app.index(end)]
    if "innerHTML" in block or "fetch(" in block:
        errors.append("search resolution must not build markup from strings or load data")
    if re.search(r"\d{2,}[,.]\d|\b(count|ratings?|proba|p10|p|lo|hi|x|y)\s*:\s*-?\d", block):
        errors.append("search context must not carry counts, probabilities or coordinates")
    if not 4 <= len(re.findall(r"\{ term: '", block)) <= 12:
        errors.append("source context must stay a small curated list")
    for needle in ['id="searchAnnounce" role="status" aria-live="polite"', 'aria-describedby="searchScope"']:
        if needle not in html:
            errors.append(f"search accessibility markup missing: {needle}")
    if not re.search(r'id="searchResolution"[^>]*\bhidden\b', html):
        errors.append("search result panel must start hidden")
    if "setTimeout" not in app or "lastAnnounced" not in app:
        errors.append("search announcements must be debounced and de-duplicated")
    if "event.key === '/'" not in app:
        errors.append("keyboard / shortcut lost")
    node = shutil.which("node")
    if not node:
        return errors + ["node is required to run the search matrix"]
    interventions = (ROOT / "data" / "interventions.json").read_text(encoding="utf-8")
    run = subprocess.run([node, "-e", block + HARNESS, interventions, json.dumps([c[0] for c in SEARCH_MATRIX])],
                         capture_output=True, text=True, timeout=30)
    if run.returncode != 0:
        return errors + [f"search matrix could not run: {run.stderr.strip()[:300]}"]
    results = json.loads(run.stdout)
    for (query, expected, must, mustnot), got in zip(SEARCH_MATRIX, results):
        if got["state"] != expected:
            errors.append(f"search {query!r}: expected {expected}, got {got['state']}")
            continue
        if expected == "empty":
            if got["view"] is not None:
                errors.append("empty search must leave the page unchanged")
            continue
        copy = " ".join(str(got["view"].get(k) or "") for k in ("label", "title", "body", "secondary"))
        for needle in must:
            if needle not in copy:
                errors.append(f"search {query!r}: missing {needle!r}")
        for needle in mustnot:
            if needle.lower() in copy.lower():
                errors.append(f"search {query!r}: forbidden {needle!r}")
        if (expected in ("reviewed", "broader")) != bool(got["actions"]):
            errors.append(f"search {query!r}: record actions only for reviewed or related evidence")
    by_q = {g["q"]: g for g in results}
    if by_q["Creatine"]["actions"] != ["creatine"] or by_q["Weightlifting"]["actions"] != ["physical-activity"]:
        errors.append("search actions must open the matching reviewed record")
    return errors


def check_community_map(app: str, html: str) -> list[str]:
    errors: list[str] = []
    block = app[app.index("const COMMUNITY_EXAMPLES"):app.index("const REGIONS")]
    rows = re.findall(r"\{ name: '([^']+)', count: (\d+), p: ([\d.]+), lo: ([\d.]+), hi: ([\d.]+) \}", block)
    if not 6 <= len(rows) <= 8:
        errors.append(f"community map must cite 6–8 published values (found {len(rows)})")
    found = {name: (int(c), float(p), float(lo), float(hi)) for name, c, p, lo, hi in rows}
    if found != CITED:
        errors.append(f"community map values differ from the verified 2022 citation set: {sorted(set(found.items()) ^ set(CITED.items()))}")
    for name, (_, p, lo, hi) in found.items():
        if not lo <= p <= hi:
            errors.append(f"{name}: value outside its interval")
        if name.lower() in HIGH_RISK_NAMES or "doing math" in name.lower():
            errors.append(f"{name} must not be placed on the 2022 map")
    regions = re.search(r"const REGIONS = \{ countSplit: (\d+), pSplit: ([\d.]+), uncommonOften: (\d+), commonRarely: (\d+), elsewhere: (\d+) \}", app)
    if not regions or regions.groups() != ("300", "0.02", "18", "20", "78"):
        errors.append("map regions must use the published thresholds (300 ratings, 0.02) and counts 18 / 20 / 78")
    elif sum(int(v) for v in regions.groups()[2:]) != 116:
        errors.append("region counts must cover the 116 plotted items")
    if "Math.log10" not in app:
        errors.append("community map must use logarithmic axes")
    for needle in ["Number of ratings →", "Reported life-changing probability →", 'role="img"', 'aria-labelledby="community-title community-desc"']:
        if needle not in app + html:
            errors.append(f"community map labelling missing: {needle}")
    if "<table" not in html or 'id="mapKeyBody"' not in html:
        errors.append("every plotted value must also be available as a table")
    return errors


def visible_text(html: str) -> str:
    p = Inspector()
    p.feed(html)
    return html_lib.unescape(" ".join(p.visible))


def check_copy(html: str, app: str) -> list[str]:
    errors: list[str] = []
    page = visible_text(html)
    public = (page + " " + js_user_strings(app)).lower()
    for phrase in BANNED_PHRASES:
        if re.search(rf"(?<![a-z]){re.escape(phrase)}", public):
            errors.append(f"product or visitor-directed language on the public page: {phrase!r}")
    if SECOND_PERSON.search(page + " " + js_user_strings(app)):
        errors.append("public copy must not address the reader")
    # Reviewed-evidence text shown on the page follows the same impersonal voice.
    for name in ("interventions.json", "claims.json", "sources.json"):
        shown = json.dumps(json.loads((ROOT / "data" / name).read_text(encoding="utf-8")), ensure_ascii=False)
        if SECOND_PERSON.search(shown):
            errors.append(f"data/{name} addresses the reader")
    for label in ["Life-changing probability", "Seven things that stand out", "All community-chart figures on this page are derived from the published 2022 data.",
                  "Life-changing probability is the modeled share of ratings at the top of the scale"]:
        if label not in page:
            errors.append(f"plain-language label missing: {label!r}")
    for label in ["Uncommon, often life-changing", "Common, rarely life-changing", "Reported life-changing probability →", "'Life-changing probability →'"]:
        if label not in app:
            errors.append(f"map label missing: {label!r}")
    if SAFETY_LINE not in page:
        errors.append("neutral information-only line missing")
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9,.'’\-]*", page))
    if words > 1100:
        errors.append(f"visible copy budget exceeded: {words} words (limit 1,100)")
    hero = re.search(r'<section class="hero".*?</section>', html, re.S).group(0)
    hero_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9,.'’\-]*", re.sub(r"<[^>]+>", " ", hero)))
    if hero_words > 16:
        errors.append(f"first screen must stay short before the map ({hero_words} hero words)")
    after_hero = html[html.index(hero) + len(hero):]
    if not re.match(r'\s*<section class="chapter map-chapter" id="map"', after_hero):
        errors.append("the community map must follow the hero directly")
    for name in HIGH_RISK_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", public):
            errors.append(f"named high-risk substance on the public page: {name}")
    for raw in ["count_without_ssc", "proba_life_changing", "results_summary", ".csv"]:
        if raw in public:
            errors.append(f"raw community dataset reference: {raw}")
    for fact in INSIGHT_FACTS:
        if fact not in page:
            errors.append(f"insight fact missing: {fact!r}")
    if len(re.findall(r'<li class="insight[ "]', html)) not in range(6, 9):
        errors.append("What stands out must hold 6–8 observations")
    data = re.search(r'<section class="chapter" id="data".*?</section>', html, re.S).group(0)
    data_text = html_lib.unescape(" ".join(re.sub(r"<[^>]+>", " ", data).split()))
    for fact in DATA_FACTS:
        if fact not in data_text:
            errors.append(f"data-about-data figure missing: {fact!r}")
    if "4.49" in data_text or "4.5×" in data_text:
        errors.append("the all-rows 4.49× figure must not describe the 116 plotted items")
    if "later" in data_text.lower():
        errors.append("no data-about-data figure may describe the later image")
    snap = re.search(r'<section class="chapter" id="snapshots".*?</section>', html, re.S).group(0)
    snap_text = html_lib.unescape(" ".join(re.sub(r"<[^>]+>", " ", snap).split()))
    for needle in ["Published data vs. later image", "Published 2022 data", "Public table and reproducible values",
                   "Later image · underlying data unavailable", "Additional labels, no public dataset", "125", "116", "Doing Math",
                   "A separate later image contains labels that are not present in the published 2022 dataset.",
                   "Its underlying data is unavailable, so no numerical values are taken from it."]:
        if needle not in snap_text:
            errors.append(f"published-data vs. later-image distinction missing: {needle!r}")
    # Doing Math never carries a figure: every sentence that names it is free of digits other than the year 2022.
    vp = Inspector()
    vp.feed(html)
    units = [html_lib.unescape(t) for t in vp.visible] + [a or b for a, b in re.findall(r"'([^'\\\n]{4,})'|`([^`]{4,})`", app)]
    for sentence in (x for u in units for x in re.split(r"(?<=[.!?])\s+", u)):
        if "doing math" in sentence.lower() and re.search(r"\d", sentence.replace("2022", "")):
            errors.append(f"Doing Math sentence carries a number: {sentence[:90]!r}")
    # Whole later-image blocks carry no figures: the Doing Math observation and the later snapshot card.
    for pattern, label in [(r'<li class="insight insight-feature">.*?</li>', "Doing Math observation"),
                           (r'<article class="snapshot snapshot-later">.*?</article>', "later-image snapshot")]:
        m = re.search(pattern, html, re.S)
        if not m:
            errors.append(f"{label} missing")
        elif re.search(r"\d", html_lib.unescape(re.sub(r"<[^>]+>", " ", m.group(0))).replace("2022", "")):
            errors.append(f"{label} carries a number; the later image has no documented values")
        else:
            text = html_lib.unescape(" ".join(re.sub(r"<[^>]+>", " ", m.group(0)).split())).lower()
            # No rank, position or probability, and nothing implying the later data can be read.
            for word in ["rank", "top", "most", "upper", "lower", "left", "right", "probab", "%", "rating", "coordinate",
                         "data is available", "dataset is available", "data are available"]:
                if re.search(rf"(?<![a-z]){re.escape(word)}", text):
                    errors.append(f"{label} implies a rank, position, figure or available data: {word!r}")
            if "underlying data is unavailable" not in text:
                errors.append(f"{label} must say the later image's underlying data is unavailable")
    insight = re.search(r'<li class="insight insight-feature">.*?</li>', html, re.S)
    if insight and "separate later image" not in insight.group(0):
        errors.append("the Doing Math observation must explain the later image on its own, before the comparison section")
    return errors


def public_surface(html: str) -> str:
    """Every string a visitor, screen reader or share card can meet: text, sr-only text and attribute values."""
    html = re.sub(r"<!--.*?-->|<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.S)
    attrs = re.findall(r'\b(?:content|alt|title|aria-label|placeholder|value)="([^"]*)"', html)
    text = re.sub(r"<[^>]+>", " ", html)
    return html_lib.unescape(" ".join((text + " " + " ".join(attrs)).split()))


def check_context(html: str, app: str) -> list[str]:
    errors: list[str] = []
    explore = (WEB / "explore.html").read_text(encoding="utf-8")
    surface = public_surface(html) + " " + public_surface(explore) + " " + js_user_strings(app)
    low = surface.lower()
    for phrase in CONTEXT_LEAKS:
        if re.search(rf"(?<![a-z]){re.escape(phrase)}", low):
            errors.append(f"context-dependent public copy: {phrase!r}")
    for phrase in CONTEXT_REQUIRED:
        if phrase not in surface:
            errors.append(f"self-contained source explanation missing: {phrase!r}")
    if "doing math" in (re.search(r'placeholder="([^"]*)"', html) or [None, ""])[1].lower():
        errors.append("the search placeholder must use familiar examples, not the later-image label")
    return errors


# Readability floor: visible text stays at about 11px (.68rem = 10.88px) or larger.
FLOOR_PX = 10.88
FLOOR_SELECTORS = [".eyebrow", ".badge", ".map-caption", ".map-key thead th", "#communityMap .tick", "#communityMap .region-label",
                   "#communityMap .axis-title", "#communityMap .dot-index", ".resolution-label", ".meter-label", ".meter-word",
                   ".evidence-head", ".source-list span", ".method dt", ".fine", ".receipt-label", ".rho-tick", ".width-value"]


def check_readability() -> list[str]:
    errors: list[str] = []
    css = re.sub(r"/\*.*?\*/", "", (WEB / "styles.css").read_text(encoding="utf-8"), flags=re.S)
    seen: set[str] = set()
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = m.group(1).strip().splitlines()[-1].strip(), m.group(2)
        seen.update(s.strip() for s in selector.split(","))
        for decl in re.findall(r"font(?:-size)?\s*:\s*([^;]+)", body):
            for num, unit in re.findall(r"(\d*\.?\d+)(rem|px)\b", decl):
                if float(num) * (16 if unit == "rem" else 1) < FLOOR_PX:
                    errors.append(f"readability floor: {selector} uses {num}{unit}")
    for selector in FLOOR_SELECTORS:
        if selector not in seen:
            errors.append(f"readability floor: guarded selector {selector} not found")
    if "prefers-reduced-motion" not in css:
        errors.append("reduced-motion support missing")
    for rule, needle in [(".chapter", "text-align: center"), (".hero", "text-align: center"), (".search-resolution", "text-align: center")]:
        m = re.search(re.escape(rule) + r"\s*\{([^}]*)\}", css)
        if not m or needle not in m.group(1):
            errors.append(f"centered spine lost: {rule} needs {needle}")
    return errors


def main() -> int:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    p = Inspector()
    p.feed(html)
    errors: list[str] = []
    missing = REQUIRED_IDS - set(p.ids)
    if missing:
        errors.append(f"missing required IDs: {sorted(missing)}")
    if len(p.ids) != len(set(p.ids)):
        errors.append("duplicate element IDs")
    if p.lang != "en" or p.h1 != 1:
        errors.append("html lang must be en with exactly one h1")
    positions = [html.find(f'id="{sid}"') for sid in SECTION_ORDER]
    if -1 in positions or positions != sorted(positions):
        errors.append(f"sections must appear in order: {' → '.join(SECTION_ORDER)}")
    if p.nav != NAV:
        errors.append(f"navigation must be exactly Map · Insights · Evidence · Sources (found {p.nav})")
    for ref in p.scripts + p.styles:
        if ref.startswith(("http://", "https://", "//")):
            errors.append(f"external runtime dependency not allowed: {ref}")
        elif not (WEB / ref).resolve().exists():
            errors.append(f"missing local asset: {ref}")
    if 'class="skip-link" href="#map"' not in html:
        errors.append("skip link to the map missing")
    if 'id="evidenceList" aria-live="polite"' not in html:
        errors.append("evidence list must announce search changes politely")
    for needle in [f'rel="canonical" href="{CANONICAL}"', f'property="og:url" content="{CANONICAL}"', "social-preview.png"]:
        if needle not in html:
            errors.append(f"share metadata missing: {needle}")
    for token in ("history.pushState", "syncDetailFromLocation", "popstate", "hashchange", "showModal"):
        if token not in app:
            errors.append(f"record deep-link contract missing: {token}")
    if "innerHTML" in app:
        errors.append("app.js must build the page with DOM methods, not innerHTML")
    for token in ("Limitations", "Safety context", "Sources", "Reviewed ${item.reviewed_at}", "source_claims", "limitations"):
        if token not in app:
            errors.append(f"reviewed record detail must keep {token!r}")
    if set(re.findall(r"fetch\('([^']+)'\)", app)) != {"../data/interventions.json", "../data/claims.json", "../data/sources.json"}:
        errors.append("reviewed evidence must come only from data/*.json")
    if 'href="./explore.html"' in html:
        errors.append("the main page must not link to the compatibility route")
    errors += check_copy(html, app)
    errors += check_context(html, app)
    errors += check_community_map(app, html)
    errors += check_search(html, app)
    errors += check_readability()
    if errors:
        print("SITE TEST: FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("SITE TEST: PASS — single-page structure, copy, cited values, search, evidence access and readability verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
