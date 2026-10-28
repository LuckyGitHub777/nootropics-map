# Changelog

## 0.4.0 — 2026-10-28

- Rebuilt the public experience as one page ordered around the community chart: community map, what stands out, two snapshots, data about the data, evidence check, and sources. The first screen leads with the question and the map.
- Added an original community map: number of ratings against the reported chance of a life-changing rating on logarithmic axes, the published plotting regions (18 and 20 of the 116 plotted items), and seven cited 2022 items with their model intervals, plus a table of every value shown. Neither version of the community chart is reproduced.
- Replaced the 47-idea guided reading with seven observations, including behaviors ranking among compounds, caffeine's volume without high reported impact, familiar supplements in the common-but-rarely-a-10 region, and Doing Math in the later image.
- Presented the published 2022 analysis and the later supplied image as two snapshots. Doing Math is described as one of the most prominent labels in the later image, with no values assigned to it.
- Reduced data about the data to its figures: 125 → 116 plotted, ρ ≈ 0.14, and about 4× wider intervals for sparse items.
- Kept the five reviewed evidence records, with claims, maturity, confidence, limitations, safety context, sources, and review dates, as a secondary evidence check with record links.
- Simplified search labels to Reviewed, Related evidence, 2022 chart, Later image, and Not in the current index.
- Removed product and process language from the public page and replaced visitor-directed advice with a neutral information-only line.
- The former guided-reading URL now redirects old section links into the main page.
- Reviewed evidence records unchanged; no upstream raw community dataset imported.

## 0.3.0 — 2026-10-27

- Added source-aware search with five states: reviewed record, broader reviewed record, published 2022 community source, later supplied image, and not mapped in this release. An exact reviewed record and a broader reviewed relationship (for example, Weightlifting → Physical activity) each open the reviewed record. Source-only terms explain their source state without offering a record action.
- Kept the published 2022 analysis and the later supplied image as separate source states in search. "Not mapped in this release" means not mapped by this product, not absent from any upstream source.
- Added a "What the data says about itself" evidence-literacy section to the guided reading, recomputed from the published 2022 result table and plotting code:
  - 125 result-table items become 116 plotted.
  - Rating volume and modeled life-changing probability have only a weak rank relationship across the plotted items (Spearman ρ ≈ 0.14).
  - Median model intervals are about four times wider for sparsely rated plotted items than for widely rated ones.
  - Precision is not validity: more ratings narrow an estimate but do not add randomization, blinding, placebo control, representative sampling, or causal inference.
- Raised small visible labels across the evidence map, receipts, and guided reading to a readability floor of about 11px without changing map geometry. Two geometry-bound labels keep their size: the mobile map axis ticks, whose words also appear in the map key and axis captions, and the guided-reading orbit's centre caption, which must fit inside its circle.
- Imported no upstream raw community dataset and changed no reviewed evidence record. Search context is a small curated list of names with no counts, coordinates, or rankings.
- Added regression coverage for the five search states, data-about-data figures and source attribution, and the readability floor.

## 0.2.0 — 2026-10-27

- Added a guided-reading page (`explore.html`) that explains the community Nootroflix chart in 47 ideas across eight branches, with simple and detailed reading depth and keyboard navigation.
- Added a side-by-side comparison of community signal and reviewed evidence, claim-by-claim pathways, and expandable evidence receipts with status, source support, limitations, safety context, and review date.
- The page reads every reviewed claim and source from `data/*.json`; no evidence is duplicated in page code.
- Kept the community-signal layer out of the product until a provenance-complete dataset exists; the page describes the chart in words without reproducing its placements or naming high-risk substances.
- Linked the evidence map header to the guided reading and added regression coverage for structure, data sourcing, the 47-idea reading, palette parity, and the safety boundary.
- Separated the published 2022 analysis (36,163 ratings, 2,802 people, 125-item result table, 116 plotted items) from a later supplied chart image whose dataset is not published; Doing Math and the negative y-axis tick are attributed only to the later image.
- Corrected source-chart wording: exact 300-rating and 2% thresholds from the published code, low double-digit minimum counts, published uncertainty intervals, and the separate side-effect field.
- Framed creatine as different questions (cognitive self-report versus a strength and power claim), not a disagreement.
- Centered the Explore, Evidence Library, and Trust Architecture sections on one visual spine at every width.
- Documented the community-data reuse boundary in `docs/source-policy.md`; no upstream raw community data is redistributed.
- Added regression checks for source-state separation, stale wording, cross-project terminology, and centered layout.

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
