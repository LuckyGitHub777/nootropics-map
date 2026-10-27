#!/usr/bin/env python3
"""Structural, data-sourcing, and safety-boundary checks for the guided-reading page."""
from __future__ import annotations
import hashlib
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
RESERVED_TERM_HASHES = {
    "2af412630e50a8e1a8f9d02077a88db5f8134d9f365969c2c2fb0cd274538ce4",
    "35ac9d9b71ccabaa9035054adb7db03ad3fb325c46337ab18c9a2918999d9300",
}


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


# Data-about-data diagnostics, recomputed from the published 2022 result table and plotting code
# (life-changing plot: count_without_ssc > 10, x = count). Plotted subset only: 125 rows -> 116 plotted;
# Spearman(count, proba_life_changing) = 0.1415; median interval width 0.0484 (count < 50, n = 20)
# vs 0.0123 (count >= 500, n = 20) = 3.92x. The 4.49x figure uses all 125 rows and must not appear here.
DAD_REQUIRED = [
    "published 2022", "125 result-table items", "116 plotted", "more than 10 new", "spearman ρ ≈ 0.14",
    "fewer than 50 ratings", "500 or more ratings", "20 items · median width ≈ 0.048", "20 items · median width ≈ 0.012",
    "about 4× wider", "≈3.9×", "median model interval width", "not the size of any effect",
    "weak and positive", "precision", "validity", "randomization", "blinding", "placebo control",
    "representative sampling", "causal inference", "more ratings are not better scientific evidence",
]
DAD_FORBIDDEN = ["4.49", "4.5×", "no relationship", "zero relationship", "independen", "data proves", "best",
                 "winner", "most effective", "top intervention", "causes", "ten or fewer", "handful"]


def check_data_about_data(html: str, css: str) -> list[str]:
    errors: list[str] = []
    start = html.find('<section id="dataAboutData"')
    if start == -1:
        return ["data-about-data section missing"]
    section = html[start:html.index("</section>", start)]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", section)).replace("&rsquo;", "’").lower()
    text = re.sub(r"\s+", " ", text)
    for needle in DAD_REQUIRED:
        if needle.lower() not in text:
            errors.append(f"data about data: missing {needle!r}")
    for needle in DAD_FORBIDDEN:
        if needle.lower() in text:
            errors.append(f"data about data: forbidden wording {needle!r}")
    # Every quantitative figure belongs to the published 2022 analysis; the later image is only named to exclude it.
    for sentence in re.split(r"(?<=[.!?])\s", text):
        if "later" in sentence and not re.search(r"\bnone\b|\bnot\b|undocumented", sentence):
            errors.append("data about data: a figure is attributed to the later supplied image")
    if "describes the later supplied image" not in text or "none of it" not in text:
        errors.append("data about data: must state that no figure describes the later supplied image")
    # Numbers must be internally consistent with each other.
    nums = {k: re.search(p, text) for k, p in {"rows": r"(\d+) result-table items", "plotted": r"(\d+) plotted",
             "rho": r"ρ ≈ (0\.\d+)", "low": r"median width ≈ (0\.\d+)"}.items()}
    if not all(nums.values()):
        errors.append("data about data: figures not stated in text")
    else:
        rows, plotted = int(nums["rows"].group(1)), int(nums["plotted"].group(1))
        widths = [float(w) for w in re.findall(r"median width ≈ (0\.\d+)", text)]
        if (rows, plotted) != (125, 116) or "nine items left off" not in text:
            errors.append(f"data about data: expected 125 rows and 116 plotted (nine left off), got {rows}/{plotted}")
        if abs(float(nums["rho"].group(1)) - 0.1415) > 0.006:
            errors.append(f"data about data: rho {nums['rho'].group(1)} does not match 0.1415")
        if len(widths) != 2 or abs(widths[0] - 0.0484) > 0.0006 or abs(widths[1] - 0.0123) > 0.0006:
            errors.append(f"data about data: interval widths {widths} do not match 0.048 / 0.012")
    if "<canvas" in section or "<script" in section or "style=" in section:
        errors.append("data about data: must stay static semantic markup without inline styles")
    if not re.search(r'<h2 id="dadTitle">', section) or section.count("<h3>") != 4:
        errors.append("data about data: needs one h2 and four h3 findings")
    if section.count('class="sr-only">is not<') != 4:
        errors.append("data about data: ≠ marks need spoken equivalents")
    for selector, value in {".iw-high": "width: 25.53%", ".iw-low": "width: 100%", ".rho-mark": "left: 57.08%"}.items():
        rule = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
        if not rule or value not in rule.group(1):
            errors.append(f"data about data: {selector} must encode {value} (0.0123/0.0484 and (0.1415+1)/2)")
    if html.index('id="dataAboutData"') > html.index('id="lenses"') or html.index('id="sourceState"') > html.index('id="dataAboutData"'):
        errors.append("data about data: must sit between the source states and signal-versus-evidence")
    if 'href="#dataAboutData"' not in html:
        errors.append("data about data: navigation link missing")
    return errors


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

    # Source fidelity: the published 2022 analysis and the later supplied chart image are separate states.
    page_text = html + "\n" + js
    lowered = page_text.lower()

    def windows(term: str, radius: int = 220):
        return [lowered[max(0, m.start() - radius): m.end() + radius] for m in re.finditer(re.escape(term.lower()), lowered)]

    if "published 2022" not in lowered or "later supplied image" not in lowered or 'id="sourcestate"' not in lowered:
        errors.append("source-state panel must name the published 2022 analysis and the later supplied image")
    for stale in ["ten or fewer", "handful", "three hundred", "40 hz", "−0.006", "-0.006", "disagreement is information"]:
        if stale in lowered:
            errors.append(f"stale or conflated wording returned: {stale!r}")
    def sentences(term: str):
        found = []
        for m in re.finditer(re.escape(term.lower()), lowered):
            left = max(lowered.rfind(ch, 0, m.start()) for ch in ".'\n>")
            rights = [i for i in (lowered.find(ch, m.end()) for ch in ".'\n<") if i != -1]
            found.append(lowered[left + 1:min(rights) if rights else len(lowered)])
        return found

    for sentence in sentences("doing math"):
        if "later" not in sentence:
            errors.append("Doing Math must only be attributed to the later supplied image (same sentence)")
            break
    for window in windows("36,163"):
        if "2022" not in window and "2016 survey" not in window:
            errors.append("36,163 must be attributed to the published 2022 analysis")
            break
    for window in sentences("negative bottom tick"):
        if "later" not in window:
            errors.append("the negative tick belongs to the later supplied image")
            break
    for fact in ["125 items", "116", "300", "2%"]:
        if fact not in page_text:
            errors.append(f"published-code fact missing: {fact}")
    if 'id="differentquestions"' not in lowered or "different questions" not in lowered:
        errors.append("creatine must be framed as different questions, not a disagreement")
    errors.extend(check_data_about_data(html, css))

    # Unrelated-project terminology is matched by hashed word n-grams so the deny-list itself stays private.
    for path in WEB.glob("*"):
        if not (path.is_file() and path.suffix in {".html", ".js", ".css"}):
            continue
        words = re.sub(r"[^a-z0-9]+", " ", path.read_text(encoding="utf-8").lower()).split()
        grams = {" ".join(words[i:i + n]) for n in (2, 3) for i in range(len(words) - n + 1)}
        if any(hashlib.sha256(g.encode()).hexdigest() in RESERVED_TERM_HASHES for g in grams):
            errors.append(f"unrelated-project terminology on public surface: {path.name}")

    if errors:
        print("GUIDED READING TEST: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1
    print("GUIDED READING TEST: PASS — structure, data sourcing, 47-idea reading, and safety boundary verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
