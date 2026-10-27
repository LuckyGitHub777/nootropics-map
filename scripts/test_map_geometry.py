from pathlib import Path

app = Path('web/app.js').read_text(encoding='utf-8')
errors = []
checks = {
    "compact safe margins": "{ left: 58, right: 28, top: 46, bottom: 68 }",
    "desktop safe margins": "{ left: 90, right: 70, top: 58, bottom: 70 }",
    "bounded coordinates": "const clamp = (value, min, max)",
    "mobile inward layout": "{ x:-24, y:22 }",
    "desktop inward layout": "{ x:-180, y:82 }",
    "right-edge label flip": "const labelOnLeft = !compact && xRank === 3",
    "mobile y-axis gutter": "x:compact ? 31 : 52",
}
for label, needle in checks.items():
    if needle not in app:
        errors.append(f"missing map geometry invariant: {label}")

html = Path('web/index.html').read_text(encoding='utf-8')
styles = Path('web/styles.css').read_text(encoding='utf-8')
caption = '<div class="axis-caption x-axis">Evidence maturity →</div>'
key = '<div id="mapKey" class="map-key" aria-label="Map key"></div>'
if caption not in html or key not in html or html.index(caption) > html.index(key):
    errors.append("mobile x-axis caption must precede the map key in document flow")
mobile_flow = [
    ".x-axis {",
    "position:static; left:auto; bottom:auto; transform:none;",
    "margin:.15rem 0 .55rem; text-align:center;",
    ".map-key { display:grid; gap:.55rem; margin:0 .15rem; }",
]
for needle in mobile_flow:
    if needle not in styles:
        errors.append(f"missing mobile caption/key invariant: {needle}")
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('Map geometry regression: PASS')
