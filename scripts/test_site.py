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
SECTION_ORDER = ["map", "insights", "evidence", "sources"]
# Sections retired from the page; their old anchors land on the section that now carries the information.
RETIRED_ANCHORS = {"snapshots": "map", "data": "insights"}
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
                 "doing math changes", "later supplied image", "supplied", "source state",
                 "published state", "snapshot", "current index", "current release", "upstream dataset", "upstream",
                 "visibly different places", "undocumented", "neither version", "has moved", "no reviewed record yet",
                 "new ratings",
                 # One chart: no second dataset, chart version or image is ever described to the visitor.
                 "published 2022", "2022 chart", "2022 data", "2022 dataset", "published data vs", "later image",
                 "separate later image", "separate image", "another image", "later chart", "later dataset",
                 "another dataset", "other dataset", "set of data", "chart version", "underlying data is unavailable",
                 "underlying data unavailable", "which figures can be checked", "a later image includes",
                 "data about the data", "inclusion filter", "not every result is plotted",
                 # Informational voice: describe the information, do not editorialize or instruct.
                 "community signal", "different story", "check the evidence",
                 "follow the evidence", "read carefully", "checked against the evidence"]
# Analytics that only make sense against one particular underlying result-table state stay off the page.
SOURCE_STATE_ANALYTICS = [r"36,163", r"2,802", r"(?<![\d,.])125(?![\d,])", r"(?<![\d,.])116(?![\d,])", r"ρ", r"≈\s*4×", r"≈\s*3\.9×",
                          r"<\s*50 ratings", r"500\+ ratings", r"0\.048", r"(?<![\d.])0\.012"]
CONTEXT_REQUIRED = ["Community map", "Selected items from the community chart",
                    "Reported life-changing impact across behaviors, supplements and other interventions.",
                    "Community reports and scientific evidence answer different questions."]
SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself)\b", re.I)

# The seven cited map values (result table, verified 2026-10-28 against results_summary.csv in the
# analysis repository). Not a dataset; a small attributed citation set.
CITED = {
    "Weightlifting": (567, 0.121, 0.093, 0.153),
    "Trying to get more sleep": (993, 0.075, 0.060, 0.093),
    "Meditation": (429, 0.066, 0.046, 0.093),
    "Caffeine": (2553, 0.030, 0.025, 0.037),
    "Creatine": (1153, 0.014, 0.010, 0.020),
    "Theanine": (1322, 0.013, 0.009, 0.018),
    "Omega-3": (956, 0.010, 0.006, 0.014),
}
# Observations read directly from the chart, qualitative and in this order.
INSIGHT_HEADINGS = ["Behaviors appear alongside compounds", "Popularity and reported impact are different",
                    "Common does not mean life-changing", "The chart summarizes reported experience",
                    "Scientific evidence answers a different question"]
INSIGHT_FACTS = ["Weightlifting, sleep, meditation and Doing Math appear in the same landscape as supplements and other interventions.",
                 "Positions reflect how people rated their own experience. They do not establish efficacy, causation or safety."]


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
    ("Creatine", "reviewed", ["Reviewed evidence", "Creatine", "claim, limitations and sources", "Also in the community chart.", "Different questions."], []),
    ("Weightlifting", "broader", ["Related evidence", "Physical activity", "broader than the searched term"], ["agree", "confirm", "contradict"]),
    ("Caffeine", "chart", ["Chart item", "Caffeine appears in the community chart.",
                           "There is no reviewed evidence record for this item on the site.", "not proof of efficacy or safety"], ["yet", "2022"]),
    ("Omega-3", "chart", ["Chart item", "Omega-3"], []),
    ("Doing Math", "chart", ["Chart item", "Doing Math appears in the community chart.",
                             "There is no reviewed evidence record for this item on the site.", "not proof of efficacy or safety"],
     ["image", "2022", "dataset", "later", "separate", "version", "absent", "rating", "0.", "rank", "probability", "underlying"]),
    ("Charlie Sheen", "not-mapped", ["No matching entry", "Search covers the reviewed evidence and selected items from the community chart."],
     ["not in the source", "does not exist", "no evidence exists", "release", "index", "upstream", "dataset"]),
    ("  cReAtInE  ", "reviewed", ["Creatine"], []),
    ("creat", "reviewed", ["Creatine"], []),
    ("WEIGHT", "broader", ["Physical activity"], []),
    ("caff", "chart", ["Caffeine"], []),
    ("math", "chart", ["Doing Math"], []),
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
        if got["view"] is None:
            errors.append(f"search {query!r}: state {got['state']} has no public wording")
            continue
        link = got["view"].get("link") or {}
        copy = " ".join(str(got["view"].get(k) or "") for k in ("label", "title", "body", "secondary")) + " " + str(link.get("text") or "")
        if link and link.get("href", "").lstrip("#") not in SECTION_ORDER:
            errors.append(f"search {query!r}: link must point to a section on the page")
        for needle in must:
            if needle not in copy:
                errors.append(f"search {query!r}: missing {needle!r}")
        for needle in mustnot:
            if needle.lower() in copy.lower():
                errors.append(f"search {query!r}: forbidden {needle!r}")
        if (expected in ("reviewed", "broader")) != bool(got["actions"]):
            errors.append(f"search {query!r}: record actions only for reviewed or related evidence")
    by_q = {g["q"]: g for g in results}
    # One chart: every chart-only item, Doing Math included, resolves to the same state with the same wording.
    states = {g["state"] for g in results}
    if not states <= {"reviewed", "broader", "chart", "not-mapped", "typing", "empty"}:
        errors.append(f"search exposes retired states: {sorted(states)}")
    dm, caf = by_q["Doing Math"]["view"], by_q["Caffeine"]["view"]
    if not dm or not caf:
        errors.append("Doing Math and Caffeine must both resolve as chart items")
    elif (dm["label"], dm["secondary"], dm["body"].replace("Doing Math", "X")) != (caf["label"], caf["secondary"], caf["body"].replace("Caffeine", "X")):
        errors.append("Doing Math must resolve exactly like any other chart item")
    for token in ["published-2022", "later-image", "SNAPSHOTS_LINK", "SOURCE_CONTEXT", "source:"]:
        if token in block:
            errors.append(f"search keeps a retired source-state concept: {token!r}")
    if "{ term: 'Doing Math' }" not in block or len(re.findall(r"doing math", block, re.I)) != 1:
        errors.append("Doing Math must be one ordinary chart item in search, with no special branch")
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
    regions = re.search(r"const REGIONS = \{ countSplit: (\d+), pSplit: ([\d.]+) \}", app)
    if not regions or regions.groups() != ("300", "0.02"):
        errors.append("map regions must use the chart's thresholds (300 ratings, 0.02)")
    region_block = app[app.index("const regionText"):app.index("regionText.forEach")]
    if "items" in region_block or "REGIONS." in region_block:
        errors.append("region labels must not carry item counts")
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
    if not re.search(r'<h1 id="hero-title">What changes the mind\?</h1>', html) or 'id="evidence-title">Reviewed evidence</h2>' not in html:
        errors.append("hero and evidence headings must be the plain informational versions")
    for label in ["Life-changing probability", "Five things that stand out", "Selected items from the community chart",
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
    headings = re.findall(r'<li class="insight">\s*<h3>([^<]+)</h3>', html)
    if headings != INSIGHT_HEADINGS or len(re.findall(r'<li class="insight[ "]', html)) != len(INSIGHT_HEADINGS):
        errors.append(f"What stands out must hold exactly the {len(INSIGHT_HEADINGS)} plain observations: {headings}")
    for sid in RETIRED_ANCHORS:
        if f'id="{sid}"' in html:
            errors.append(f"retired section #{sid} is still on the page")
    errors += check_doing_math(html, app)
    return errors


def check_doing_math(html: str, app: str) -> list[str]:
    """Doing Math is one ordinary chart item: named normally, never featured, never given a figure."""
    errors: list[str] = []
    css = (WEB / "styles.css").read_text(encoding="utf-8")
    if "insight-feature" in html + css or "badge" in html:
        errors.append("no observation may carry a feature class or a source badge")
    if len(re.findall(r"Doing Math", html)) != 1:
        errors.append("Doing Math is named once, as an ordinary example in an observation")
    li = re.search(r'<li class="([^"]*)">((?:(?!</li>).)*Doing Math(?:(?!</li>).)*)</li>', html, re.S)
    if not li or li.group(1) != "insight":
        errors.append("Doing Math must sit in an ordinary observation")
    else:
        text = html_lib.unescape(" ".join(re.sub(r"<[^>]+>", " ", li.group(2)).split()))
        if re.search(r"\d", text):
            errors.append("the observation naming Doing Math carries a number")
        for word in ["rank", "top", "most", "upper", "lower", "left", "right", "probab", "%", "rating", "coordinate",
                     "prominent", "absent", "only in", "image", "dataset"]:
            if re.search(rf"(?<![a-z]){re.escape(word)}", text.lower()):
                errors.append(f"the observation naming Doing Math singles it out: {word!r}")
        if sum(name in text for name in ["Weightlifting", "sleep", "meditation"]) < 2:
            errors.append("Doing Math must appear alongside other chart items, not on its own")
    vp = Inspector()
    vp.feed(html)
    units = [html_lib.unescape(t) for t in vp.visible] + [a or b for a, b in re.findall(r"'([^'\\\n]{4,})'|`([^`]{4,})`", app)]
    for sentence in (x for u in units for x in re.split(r"(?<=[.!?])\s+", u)):
        if "doing math" in sentence.lower() and re.search(r"\d", sentence):
            errors.append(f"Doing Math sentence carries a number: {sentence[:90]!r}")
    return errors


def public_surface(html: str) -> str:
    """Every string a visitor, screen reader or share card can meet: text, sr-only text and attribute values."""
    html = re.sub(r"<!--.*?-->|<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.S)
    attrs = re.findall(r'\b(?:content|alt|title|aria-label|placeholder|value)="([^"]*)"', html)
    text = re.sub(r"<[^>]+>", " ", html)
    return html_lib.unescape(" ".join((text + " " + " ".join(attrs)).split()))


SHARE_DESCRIPTION = "Reported life-changing impact across behaviors, supplements and other interventions."
SHARE_ALT = "Nootropics Map — What changes the mind?"


def check_share(html: str) -> list[str]:
    """Share metadata and the social card carry the same plain information as the page."""
    errors: list[str] = []
    for attr, name, want in [("name", "description", SHARE_DESCRIPTION), ("property", "og:description", SHARE_DESCRIPTION),
                             ("name", "twitter:description", SHARE_DESCRIPTION), ("property", "og:image:alt", SHARE_ALT),
                             ("name", "twitter:image:alt", SHARE_ALT)]:
        found = re.findall(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', html)
        if found != [want]:
            errors.append(f"share metadata {name} must be exactly {want!r} (found {found})")
    png = (WEB / "social-preview.png").read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        return errors + ["social preview must be a PNG"]
    pos, chunks = 8, []
    while pos < len(png):
        length = int.from_bytes(png[pos:pos + 4], "big")
        chunks.append(png[pos + 4:pos + 8].decode("latin-1"))
        if chunks[-1] == "IHDR" and (int.from_bytes(png[pos + 8:pos + 12], "big"), int.from_bytes(png[pos + 12:pos + 16], "big")) != (1200, 630):
            errors.append("social preview must be 1200×630")
        pos += 12 + length
    extra = sorted(set(chunks) - {"IHDR", "PLTE", "IDAT", "IEND", "sRGB", "gAMA", "pHYs"})
    if extra:
        errors.append(f"social preview carries metadata chunks: {extra}")
    return errors


def check_context(html: str, app: str) -> list[str]:
    errors: list[str] = []
    errors += check_share(html)
    explore = (WEB / "explore.html").read_text(encoding="utf-8")
    surface = public_surface(html) + " " + public_surface(explore) + " " + js_user_strings(app)
    low = surface.lower()
    for phrase in CONTEXT_LEAKS:
        if re.search(rf"(?<![a-z]){re.escape(phrase)}", low):
            errors.append(f"context-dependent public copy: {phrase!r}")
    for phrase in CONTEXT_REQUIRED:
        if phrase not in surface:
            errors.append(f"unified chart wording missing: {phrase!r}")
    # The chart is not framed by year anywhere on the page, citations included; linked sources carry their own dates.
    framing = public_surface(html) + " " + js_user_strings(app)
    if re.search(r"\b2022\b", framing):
        errors.append("the chart must not be framed by year on the public page")
    for pattern in SOURCE_STATE_ANALYTICS:
        if re.search(pattern, framing):
            errors.append(f"source-state analytic on the public page: {pattern!r}")
    retired = re.search(r"const RETIRED_ANCHORS = \{ snapshots: '(\w+)', data: '(\w+)' \};", app)
    if not retired or dict(zip(RETIRED_ANCHORS, retired.groups())) != RETIRED_ANCHORS:
        errors.append("old #snapshots and #data links must land on #map and #insights")
    if "doing math" in (re.search(r'placeholder="([^"]*)"', html) or [None, ""])[1].lower():
        errors.append("the search placeholder must use familiar examples, not the later-image label")
    return errors


# Readability floor: visible text stays at about 11px (.68rem = 10.88px) or larger.
FLOOR_PX = 10.88
FLOOR_SELECTORS = [".eyebrow", ".map-caption", ".map-key thead th", "#communityMap .tick", "#communityMap .region-label",
                   "#communityMap .axis-title", "#communityMap .dot-index", ".resolution-label", ".meter-label", ".meter-word",
                   ".evidence-head", ".source-list span", ".method dt", ".fine", ".receipt-label"]


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
