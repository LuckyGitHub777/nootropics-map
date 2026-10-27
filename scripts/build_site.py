#!/usr/bin/env python3
"""Build a GitHub Pages/custom-domain-safe static artifact in _site/."""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DATA = ROOT / "data"
OUT = ROOT / "_site"
TEXT_ASSETS = ["index.html", "styles.css", "app.js", "404.html", "favicon.svg"]
BINARY_ASSETS = ["social-preview.png"]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    # Normalize deployable text to canonical LF bytes on every operating system.
    for name in TEXT_ASSETS:
        text = (WEB / name).read_text(encoding="utf-8")
        if name == "app.js":
            text = text.replace("fetch('../data/", "fetch('./data/")
        (OUT / name).write_bytes(text.encode("utf-8"))

    for name in BINARY_ASSETS:
        shutil.copy2(WEB / name, OUT / name)

    data_out = OUT / "data"
    data_out.mkdir()
    for source in sorted(DATA.glob("*.json")):
        text = source.read_text(encoding="utf-8")
        (data_out / source.name).write_bytes(text.encode("utf-8"))

    (OUT / ".nojekyll").write_bytes(b"")
    print(f"SITE BUILD: PASS — {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
