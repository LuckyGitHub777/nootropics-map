#!/usr/bin/env python3
"""Build and verify the exact artifact intended for GitHub Pages."""
from __future__ import annotations
import json
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
        "index.html", "styles.css", "app.js", "404.html", "favicon.svg", ".nojekyll",
        "data/interventions.json", "data/claims.json", "data/sources.json",
    ]
    missing = [p for p in required if not (OUT / p).exists()]
    if missing:
        return fail(f"missing built paths: {missing}")

    html = (OUT / "index.html").read_text(encoding="utf-8")
    app = (OUT / "app.js").read_text(encoding="utf-8")
    if "../data/" in app:
        return fail("built app still escapes the Pages artifact for data")
    if "fetch('./data/" not in app:
        return fail("built app has no root-relative data fetches")
    if 'id="reviewDate"' not in html:
        return fail("review-date element missing")
    if 'href="/' in html or 'src="/' in html or "href='/" in html or "src='/" in html:
        return fail("root-absolute asset path found; project Pages path would break")

    for name in ["interventions.json", "claims.json", "sources.json"]:
        json.loads((OUT / "data" / name).read_text(encoding="utf-8"))

    print("DEPLOY TEST: PASS — root URL, project Pages path, and custom-domain artifact are structurally compatible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
