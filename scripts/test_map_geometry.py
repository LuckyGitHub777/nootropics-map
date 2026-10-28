#!/usr/bin/env python3
"""Community-map geometry: faithful log placement, published regions, and collision-safe labels."""
import math
import re
from pathlib import Path

app = Path('web/app.js').read_text(encoding='utf-8')
errors = []
checks = {
    "compact safe margins": "{ l: 68, r: 14, t: 18, b: 58 }",
    "desktop safe margins": "{ l: 92, r: 40, t: 26, b: 74 }",
    "log x placement": "Math.log10(v / xMin) / Math.log10(xMax / xMin)",
    "log y placement": "Math.log10(v / yMin) / Math.log10(yMax / yMin)",
    "y floor below every interval": "const yMin = 0.004;",
    "regions from published thresholds": "x(REGIONS.countSplit)",
    "points at exact values": "const cx = x(d.count);",
    "compact labels beside, not on, points": "x: left ? cx - 9 : cx + 9",
}
for label, needle in checks.items():
    if needle not in app:
        errors.append(f"missing map geometry invariant: {label}")

block = app[app.index('const COMMUNITY_EXAMPLES'):app.index('const REGIONS')]
rows = [(n, int(c), float(p), float(lo), float(hi)) for n, c, p, lo, hi in
        re.findall(r"\{ name: '([^']+)', count: (\d+), p: ([\d.]+), lo: ([\d.]+), hi: ([\d.]+) \}", block)]
x_min, x_max, y_min, y_max = 10, 4000, 0.004, 0.2
for name, count, p, lo, hi in rows:
    if not (x_min <= count <= x_max and y_min < lo and hi < y_max):
        errors.append(f"{name} falls outside the drawn axes")

# Every point has a direct label side on desktop and a number position on mobile.
sides = dict(re.findall(r"'([^']+)': '(left|right)'", app[app.index('const labelSide'):app.index('const labelDy')]))
for name, *_ in rows:
    if name not in sides:
        errors.append(f"{name} has no label side")

# Desktop label clearance: approximate each label box and require it to miss every other point and interval.
W, H, m = 960, 560, {'l': 92, 'r': 40, 't': 26, 'b': 74}
dy = {k: int(v) for k, v in re.findall(r"'([^']+)': (-?\d+)", app[app.index('const labelDy'):app.index('const compactDy')])}
X = lambda v: m['l'] + math.log10(v / x_min) / math.log10(x_max / x_min) * (W - m['l'] - m['r'])
Y = lambda v: H - m['b'] - math.log10(v / y_min) / math.log10(y_max / y_min) * (H - m['t'] - m['b'])
for name, count, p, lo, hi in rows:
    width = 8.4 * len(name)  # 17px serif, generous average advance
    base = Y(p) + 4 + dy.get(name, 0)
    left = sides.get(name) == 'left'
    box = (X(count) - 12 - width, X(count) - 12) if left else (X(count) + 12, X(count) + 12 + width)
    top, bottom = base - 14, base + 4
    for other, c2, p2, lo2, hi2 in rows:
        if other == name:
            continue
        ox = X(c2)
        if box[0] - 2 < ox < box[1] + 2 and not (bottom < Y(hi2) or top > Y(lo2)):
            errors.append(f"desktop label {name!r} crosses {other!r}")

if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('Map geometry regression: PASS')
