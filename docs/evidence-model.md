# Evidence Model

## Core objects

### Source
A provenance record for a publication, guideline, public-health resource, dataset, or other evidence artifact.

### Claim
A bounded statement that can be supported, qualified, contradicted, mixed, emerging, or not established.

### Intervention
A user-facing concept that groups related claims and outcomes.

## Claim status

- `supported`
- `supported_with_qualification`
- `mixed`
- `emerging`
- `not_established`
- `contradicted`

## Confidence

- `high`
- `moderate`
- `low`
- `unknown`

Confidence is not a probability and must not imply clinical certainty. It summarizes the reviewed evidence state for the exact claim as written.

## Source classes

Source class is descriptive, not automatically determinative:

- `government_guidance`
- `systematic_review`
- `meta_analysis`
- `randomized_trial`
- `observational`
- `peer_reviewed_review`
- `preclinical`
- `community_self_report`
- `other`

## Evidence receipt

Every claim record contains:

- stable claim ID;
- exact claim text;
- claim type;
- status;
- confidence;
- source IDs;
- limitations;
- last-reviewed date.

## Critical separation

A source can *say* something without Nootropics Map *endorsing* it. Source claims and Nootropics Map assessments are separate data fields by design.

## Intervention evidence band

`evidence_band` is a coarse human-reviewed summary of the maturity of the source set attached to an intervention's current bounded claims. It is **not** an effect-size estimate, probability, clinical grade, or recommendation. v0.1 deliberately limits it to `emerging`, `moderate`, and `strong` and does not numerically rank interventions within a band.

## Map semantics

The public v0.1 map renders:

- **X — evidence maturity:** the intervention's `evidence_band`;
- **Y — assessment confidence:** the most conservative confidence among the intervention's attached claims.

Confidence means confidence in the exact bounded claim as written. It does not mean that the effect is large, desirable for every person, or safe for individualized use.

## Deferred signal layer

The originating concept included crowdsourced/self-report signal discovery. That layer is intentionally **not** rendered in v0.1 because this repository does not yet contain a provenance-complete signal dataset. A future signal view requires explicit source records (for example `community_self_report`), methodology, sampling limitations, and independent uncertainty labeling before it can appear in the public map.
