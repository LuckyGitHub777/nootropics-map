#!/usr/bin/env python3
"""Public product/repository invariants for Nootropics Map."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(errors: list[str]) -> int:
    print("BRANDING TEST: FAIL")
    for error in errors:
        print(f" - {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    domain = (ROOT / "docs" / "custom-domain.md").read_text(encoding="utf-8")

    if package.get("name") != "nootropics-map":
        errors.append("package name must be nootropics-map")
    if package.get("version") != "0.1.0":
        errors.append("package version must match 0.1.0")
    if not readme.startswith("# Nootropics Map"):
        errors.append("README title must be Nootropics Map")
    if "https://luckygithub777.github.io/nootropics-map/" not in domain:
        errors.append("canonical project Pages URL missing")
    if '<title>Nootropics Map</title>' not in index:
        errors.append("web title missing")
    if 'content="Nootropics Map"' not in index:
        errors.append("Open Graph product title missing")
    canonical = "https://luckygithub777.github.io/nootropics-map/"
    if f'rel="canonical" href="{canonical}"' not in index:
        errors.append("canonical Pages URL missing from page head")
    if f'property="og:url" content="{canonical}"' not in index:
        errors.append("Open Graph canonical URL missing")
    if "social-preview.png" not in index:
        errors.append("social preview metadata missing")
    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    if 'id="mapKey"' not in index or "compactOffsets" not in app or ".map-key-item" not in styles:
        errors.append("responsive mobile map key/collision treatment missing")
    prohibited_exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = {p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in prohibited_exts}
    allowed_images = {Path("web/social-preview.png")}
    if images != allowed_images:
        errors.append(f"raster release boundary mismatch: expected {sorted(map(str, allowed_images))}, found {sorted(map(str, images))}")



    if errors:
        return fail(errors)
    print("BRANDING TEST: PASS — public product, Pages path, and release boundaries are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
