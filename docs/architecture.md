# Architecture

## Design principle

The website is an interface over structured evidence records. Presentation is never the system of record.

```text
Public sources
    ↓
Source records
    ↓
Claim records
    ↓
Evidence states + limitations
    ↓
Intervention records
    ↓
Static evidence bundle
    ↓
Web explorer
```

## Repository layers

- `data/` — canonical structured knowledge records.
- `schemas/` — machine-enforced shape contracts.
- `scripts/` — validation, public-boundary checks, and reproducible site builds.
- `web/` — static evidence-browsing experience.
- `docs/` — methodology, safety, UX, and deployment documentation.
- `.github/` — CI, issue forms, review templates, and Pages workflow.

## Why static-first

The first release uses no frontend framework or third-party runtime library. That keeps the dependency surface small, the deployment reproducible, and the public evidence bundle easy to inspect.

The presentation layer can evolve later without changing the structured evidence contract.

## Extension rule

Any future search, comparison, or answer layer must retrieve and preserve approved source/claim relationships before presentation. New features may summarize existing records, but they must not manufacture evidence, citations, confidence, or provenance.
