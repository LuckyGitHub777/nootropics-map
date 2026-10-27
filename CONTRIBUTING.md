# Contributing

Nootropics Map is a source-backed evidence-navigation project. Contributions should make the public record clearer, more inspectable, or more useful without turning the site into a recommendation engine.

## Principles

1. **Source before synthesis.** Material claims must trace to structured source records.
2. **Bound the claim.** Prefer one reviewable statement over broad conclusions.
3. **Preserve uncertainty.** `unknown`, `mixed`, and `not established` are valid outcomes.
4. **Separate evidence from effect.** Evidence maturity and confidence are not effect-size scores.
5. **No personalized medical guidance.** Do not add diagnosis, prescribing, dosing, or medication-change instructions.
6. **Do not gamify high-risk interventions.** Prescription, controlled, experimental, or high-risk records must not be rendered as consumer rankings.
7. **Respect rights and privacy.** Do not commit secrets, private data, confidential material, or third-party source files without redistribution rights.
8. **Keep the experience calm and legible.** Restraint, clarity, and accessibility take priority over decorative complexity.

## Change flow

`SOURCE → STRUCTURE → VALIDATE → RENDER → REVIEW → TEST → PR`

Before opening a pull request:

```text
npm run verify
```

A passing test proves only the scope covered by that test. Evidence changes still require human review of the source, wording, limitations, and public presentation.
