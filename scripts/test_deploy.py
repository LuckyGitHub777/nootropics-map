#!/usr/bin/env python3
"""Build and verify the exact artifact intended for GitHub Pages."""
from __future__ import annotations
import html as html_lib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"


def fail(message: str) -> int:
    print(f"DEPLOY TEST: FAIL — {message}")
    return 1


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], check=True)
    required = [
        "index.html", "styles.css", "app.js", "explore.html", "explore.js", "404.html", "favicon.svg", "social-preview.png", ".nojekyll",
        "data/interventions.json", "data/claims.json", "data/sources.json",
    ]
    missing = [p for p in required if not (OUT / p).exists()]
    if missing:
        return fail(f"missing built paths: {missing}")

    html = (OUT / "index.html").read_text(encoding="utf-8")
    canonical_text_paths = [
        "index.html", "styles.css", "app.js", "explore.html", "explore.js", "404.html", "favicon.svg",
        "data/interventions.json", "data/claims.json", "data/sources.json",
    ]
    for rel in canonical_text_paths:
        if b"\r" in (OUT / rel).read_bytes():
            return fail(f"canonical LF text artifact violated: {rel}")

    app = (OUT / "app.js").read_text(encoding="utf-8")
    if "../data/" in app:
        return fail("built app still escapes the Pages artifact for data")
    if "fetch('./data/" not in app:
        return fail("built app has no root-relative data fetches")
    if (OUT / "explore.css").exists():
        return fail("retired guided-reading stylesheet published")
    explore_html = (OUT / "explore.html").read_text(encoding="utf-8")
    explore = (OUT / "explore.js").read_text(encoding="utf-8")
    if "window.location.replace(" not in explore or "fetch(" in explore:
        return fail("compatibility route must redirect without loading data")
    if f'rel="canonical" href="https://luckygithub777.github.io/nootropics-map/"' not in explore_html or 'href="./"' not in explore_html:
        return fail("compatibility route must point to the main page")
    if 'id="reviewNote"' not in html or 'id="communityMap"' not in html:
        return fail("community map or review note missing")
    visible = " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", html)).split())
    if "What changes the mind? Reported life-changing impact across behaviors, supplements and other interventions." not in visible:
        return fail("visible hero copy mismatch")
    canonical = "https://luckygithub777.github.io/nootropics-map/"
    if f'rel="canonical" href="{canonical}"' not in html or "social-preview.png" not in html:
        return fail("canonical/share metadata missing")
    if 'href="/' in html or 'src="/' in html or "href='/" in html or "src='/" in html:
        return fail("root-absolute asset path found; project Pages path would break")

    for name in ["interventions.json", "claims.json", "sources.json"]:
        json.loads((OUT / "data" / name).read_text(encoding="utf-8"))

    print("DEPLOY TEST: PASS — root URL, project Pages path, and custom-domain artifact are structurally compatible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
