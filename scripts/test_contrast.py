#!/usr/bin/env python3
"""Contrast regression checks for the core dark-theme text tokens."""
from __future__ import annotations

TOKENS = {
    "bg": "#0a0a0a",
    "panel": "#11110f",
    "text": "#f0ede4",
    "muted": "#a6a197",
    "faint": "#8a847a",
    "accent": "#d9c8a2",
}


def luminance(value: str) -> float:
    rgb = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(channel, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main() -> int:
    checks = [
        ("text/bg", TOKENS["text"], TOKENS["bg"], 4.5),
        ("muted/bg", TOKENS["muted"], TOKENS["bg"], 4.5),
        ("faint/panel", TOKENS["faint"], TOKENS["panel"], 4.5),
        ("accent/bg", TOKENS["accent"], TOKENS["bg"], 4.5),
    ]
    failures = []
    for name, fg, bg, minimum in checks:
        value = contrast(fg, bg)
        if value < minimum:
            failures.append(f"{name}: {value:.2f}:1 < {minimum:.1f}:1")
    if failures:
        print("CONTRAST TEST: FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("CONTRAST TEST: PASS — core normal-text tokens meet or exceed 4.5:1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
