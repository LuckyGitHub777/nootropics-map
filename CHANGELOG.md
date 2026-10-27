# Changelog

## 0.1.0 — 2026-10-27

- Promoted the fully verified rc.6 candidate to the first public release.
- Preserved the source-backed evidence model, responsive map geometry, safety boundaries, and reproducible Pages deployment.
- Completed private PR/CI verification before publication.
- Completed production UX closeout with mobile methodology parity, accessible toggle states, shareable intervention links, and canonical social metadata.
- Added a first-party social preview while preserving the third-party-image exclusion boundary.
- Hardened hosted verification to validate visible hero copy and the exact deployable artifact.
- Normalized generated text artifacts to canonical LF so Pages builds are byte-reproducible across Windows and Linux.

## 0.1.0-rc.6 — 2026-10-27

- Moved the mobile x-axis caption into normal document flow directly beneath the chart and above the interactive map key.
- Removed the absolute-positioning interaction that caused the caption to overlap map-key item 5 at 375–430px widths.
- Added regression coverage requiring caption-before-key document order and the mobile flow layout.
- Supersedes rc.5 before any GitHub push.

## 0.1.0-rc.5 — 2026-10-27

- Corrected evidence-map geometry at 390px and 1440px so markers and axis labels remain inside the plot.
- Added deterministic inward slots for dense evidence cells instead of pushing collisions beyond the right edge.
- Anchored desktop labels inward for Strong-evidence points while preserving the mobile numbered key.
- Added automated map-geometry regression coverage.

## 0.1.0-rc.4 — 2026-10-27

Mobile-map refinement candidate.

### Changed
- replaced scaled-down mobile SVG labels with crisp numbered map markers and an interactive readable key;
- added collision-aware compact positioning for records that share the same evidence/confidence coordinate;
- made the SVG viewBox responsive so phone rendering preserves legible axes and touch targets;
- added regression checks requiring the responsive mobile map treatment;
- superseded rc.3 before any GitHub push because hosted visual review identified unreadable mobile label overlap.

### Verified
- evidence-reference validation;
- public-boundary scan;
- structural accessibility checks;
- contrast regression;
- repository/Pages-path invariants;
- JavaScript syntax and unit tests;
- reproducible Pages artifact and deployment-path compatibility.

## 0.1.0-rc.3 — 2026-10-27

Public-surface refinement candidate.

### Changed
- reduced the repository to product, evidence, methodology, safety, contribution, test, and deployment material appropriate for a clean public project;
- added a conventional `CONTRIBUTING.md` with evidence, safety, and review standards;
- simplified release-facing documentation and kept the public tree focused on the product, evidence, and verification surface;
- refined the visual system toward a restrained scientific-atlas aesthetic with stronger cartographic depth and hierarchy;
- strengthened public metadata and repository documentation while preserving the source-first evidence boundary;
- bumped the release candidate to `v0.1.0-rc.3`.

### Verified
- evidence-reference validation;
- public-boundary scan;
- structural accessibility checks;
- contrast regression;
- repository/Pages-path invariants;
- JavaScript syntax and unit tests;
- reproducible Pages artifact and deployment-path compatibility.

## 0.1.0-rc.2 — 2026-10-27

- locked the product name to **Nootropics Map** and repository slug to `nootropics-map`;
- retained **cognitive intervention** as the broader technical data model;
- excluded the originating third-party raster graphic from the release tree;
- established a reproducible GitHub Pages/custom-domain build.

## 0.1.0-rc.1 — 2026-10-23

- added the source → claim → evidence-state → intervention model;
- added evidence receipts, search/filtering, accessibility checks, and deployment verification;
- removed an unsupported self-report signal axis from the initial evidence view until a provenance-complete dataset exists.
