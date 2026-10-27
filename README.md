# Nootropics Map

> A source-backed visual evidence map for nootropics and cognition-related interventions.

**See the signal. Trace the evidence.**

Nootropics Map is a visual field guide to substances, behaviors, environmental inputs, and other interventions associated with cognition and performance. It is designed to help a curious reader understand what a claim means, how mature the evidence is, what remains uncertain, and where the supporting sources come from.

The public title is intentionally familiar. The underlying data model is broader than pills or supplements: sleep, exercise, light, meditation, nutrition, prescription interventions, and carefully reviewed experimental records can all be represented when the evidence and safety context justify inclusion.

## What the map is — and is not

Nootropics Map is **evidence navigation**, not a consumer leaderboard.

The interface keeps five ideas separate:

- **Evidence maturity** — how developed the source base is for a bounded claim.
- **Confidence** — how strongly the reviewed sources support that exact claim.
- **Uncertainty** — what remains unresolved, mixed, or untested.
- **Safety context** — what should not be inferred from the evidence record.
- **Provenance** — where material claims came from and when sources were reviewed.

Inclusion does not mean an intervention is proven to enhance cognition, safe for a particular person, or recommended.

## Evidence architecture

```text
SOURCE → CLAIM → EVIDENCE STATE → INTERVENTION → VISUAL EXPLANATION
```

Structured records live in `data/`. The website is a presentation layer over those records, not the source of truth.

## Run locally

Serve the repository root and open `/web/`:

```text
python -m http.server 8000
# http://localhost:8000/web/
```

The website has no frontend runtime dependencies.

## Verify

```text
npm run verify
```

The verification suite checks evidence references, public-boundary hygiene, structural accessibility, contrast, repository identity, JavaScript syntax/tests, and the exact Pages build artifact.

## Build the deployable site

```text
python scripts/build_site.py
```

The generated `_site/` is path-safe for both a GitHub project Pages URL and a future custom-domain root. `_site/` is not committed; it is rebuilt from source for deployment.

## Repository guide

- `data/` — structured sources, claims, and intervention records.
- `schemas/` — JSON shape contracts.
- `web/` — the visual evidence explorer (`index.html`) and the guided reading of the community chart (`explore.html`).
- `scripts/` — validation and reproducible build checks.
- `tests/` — behavior and data tests.
- `docs/evidence-model.md` — evidence semantics and confidence boundaries.
- `docs/source-policy.md` — source selection and provenance policy.
- `docs/safety.md` — safety and medical-information boundary.
- `docs/architecture.md` — system design.
- `docs/ux-principles.md` — visual and interaction principles.
- `docs/custom-domain.md` — Pages/custom-domain deployment notes.

## Safety boundary

Educational evidence navigation only. Nootropics Map does not diagnose, treat, prescribe, recommend individualized interventions, provide dosing guidance, or replace professional medical advice.

## License

Copyright © 2026. All rights reserved. See `LICENSE`.
