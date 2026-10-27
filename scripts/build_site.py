#!/usr/bin/env python3
"""Build a GitHub Pages/custom-domain-safe static artifact in _site/."""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DATA = ROOT / "data"
OUT = ROOT / "_site"
ASSETS = ["index.html", "styles.css", "app.js", "404.html", "favicon.svg"]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in ASSETS:
        shutil.copy2(WEB / name, OUT / name)
    shutil.copytree(DATA, OUT / "data")

    app = OUT / "app.js"
    text = app.read_text(encoding="utf-8").replace("fetch('../data/", "fetch('./data/")
    app.write_text(text, encoding="utf-8")

    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"SITE BUILD: PASS — {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
