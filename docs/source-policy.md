# Source Policy

Nootropics Map is only as credible as the trace from a public claim back to its evidence.

## Preferred source order

1. systematic reviews and meta-analyses when the question fits them;
2. clinical guidelines or authoritative public-health references;
3. randomized or controlled human studies;
4. well-designed observational human evidence;
5. preclinical evidence for mechanism/context only;
6. self-report or community data as a separate signal layer, never as clinical proof.

Source hierarchy is contextual, not mechanical. A primary trial may be more informative than an outdated review, and a mechanistic paper cannot establish a human benefit by itself.

## Record requirements

A public source record should include, when available:

- stable title and publisher/journal;
- source type;
- publication date;
- DOI or stable public URL;
- retrieval/review date;
- a bounded summary of what the source supports;
- known limitations relevant to the claim.

## Claim discipline

Claims should be narrow enough that a reviewer can answer: “Do these specific sources support this specific statement?”

Avoid:

- extrapolating animal or cell results into human benefit;
- treating association as causation;
- converting absence of evidence into evidence of absence;
- hiding contradictory findings;
- presenting popularity or novelty as efficacy;
- mirroring copyrighted full text when a citation and bounded summary are sufficient.

## Review cadence

Source links and review dates should be refreshed before a public release that materially changes an evidence assessment. Changes in confidence or status should be reviewable in version history.

## Community chart

The public site presents one community chart as one information object. Public copy explains what the chart shows; it does not describe datasets, chart versions, source states or how the chart was obtained. The rules below are internal provenance discipline, not visitor-facing copy.

1. **Numbers come only from the analysis repository.** The seven map values, their model intervals and the region thresholds come from the result table and plotting code of Troof's Nootroflix analysis (March 23, 2022). The plotting code uses logarithmic axes, plots rows with `count_without_ssc > 10`, and shades two regions: fewer than 300 ratings with a life-changing probability above 0.02, and 300 or more ratings with a probability below 0.02.
2. **Chart labels without a result-table row carry no numbers.** A label such as Doing Math may be named as an ordinary chart item, but it is never given a count, probability, position, rank or coordinate.
3. **Nothing is read from pixels.** No value or position is estimated from a chart image.

## Community data reuse boundary

- A reuse license that would allow importing or redistributing the upstream community dataset has not been established for this project. The upstream repository reviewed for verification did not include a license file.
- Do not copy third-party raw community data into this repository without explicit permission or a completed license review.
- Citing a small number of published aggregate results with attribution is not an import of the dataset. The community map cites seven result-table items with their model intervals and the region thresholds; it is an explanatory diagram, not a Community Signal layer.
- The chart image itself is not published on the site, and chart labels are named in words only.
- A future quantitative Community Signal layer still requires provenance-complete, reusable data, a documented methodology, stated sampling limitations, and uncertainty labels before it can ship.
