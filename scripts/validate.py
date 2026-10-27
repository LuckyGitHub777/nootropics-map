#!/usr/bin/env python3
"""No-dependency validation for the canonical evidence bundle."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ALLOWED_SOURCE_TYPES = {
    "government_guidance", "systematic_review", "meta_analysis", "randomized_trial",
    "observational", "peer_reviewed_review", "preclinical", "community_self_report", "other"
}
ALLOWED_STATUS = {"supported", "supported_with_qualification", "mixed", "emerging", "not_established", "contradicted"}
ALLOWED_CONFIDENCE = {"high", "moderate", "low", "unknown"}
ALLOWED_CATEGORY = {"behavior", "environment", "exercise", "nutrition", "medicine", "neurotechnology", "education", "social", "research"}
ALLOWED_BANDS = {"emerging", "moderate", "strong"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def unique_ids(records, label, errors):
    ids = [r.get("id") for r in records]
    if len(ids) != len(set(ids)):
        fail(errors, f"{label}: duplicate IDs detected")
    if any(not x for x in ids):
        fail(errors, f"{label}: missing ID")
    return set(ids)


def main() -> int:
    errors: list[str] = []
    try:
        sources = load("sources.json")
        claims = load("claims.json")
        interventions = load("interventions.json")
    except Exception as exc:
        print(f"FAIL: unable to parse JSON: {exc}")
        return 1

    source_ids = unique_ids(sources, "sources", errors)
    claim_ids = unique_ids(claims, "claims", errors)
    intervention_ids = unique_ids(interventions, "interventions", errors)

    for src in sources:
        sid = src.get("id", "<unknown>")
        if not str(sid).startswith("SRC-"):
            fail(errors, f"{sid}: source ID must start SRC-")
        if src.get("source_type") not in ALLOWED_SOURCE_TYPES:
            fail(errors, f"{sid}: invalid source_type")
        url = src.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            fail(errors, f"{sid}: source URL must be absolute HTTPS")
        if not DATE_RE.match(src.get("retrieved_at", "")):
            fail(errors, f"{sid}: invalid retrieved_at")

    for claim in claims:
        cid = claim.get("id", "<unknown>")
        if claim.get("intervention_id") not in intervention_ids:
            fail(errors, f"{cid}: unknown intervention_id {claim.get('intervention_id')}")
        if claim.get("status") not in ALLOWED_STATUS:
            fail(errors, f"{cid}: invalid status")
        if claim.get("confidence") not in ALLOWED_CONFIDENCE:
            fail(errors, f"{cid}: invalid confidence")
        refs = claim.get("source_ids", [])
        if not refs:
            fail(errors, f"{cid}: claim must have at least one source")
        for ref in refs:
            if ref not in source_ids:
                fail(errors, f"{cid}: unknown source {ref}")
        if not claim.get("limitations"):
            fail(errors, f"{cid}: limitations must be explicit")
        if not DATE_RE.match(claim.get("last_reviewed", "")):
            fail(errors, f"{cid}: invalid last_reviewed")
        source_claims = claim.get("source_claims", [])
        mapped = {entry.get("source_id") for entry in source_claims}
        missing = set(refs) - mapped
        if missing:
            fail(errors, f"{cid}: missing source_claim summaries for {sorted(missing)}")
        for entry in source_claims:
            if entry.get("source_id") not in refs:
                fail(errors, f"{cid}: source_claim references non-attached source {entry.get('source_id')}")
            if len(entry.get("summary", "").strip()) < 10:
                fail(errors, f"{cid}: source_claim summary too short")

    for item in interventions:
        iid = item.get("id", "<unknown>")
        if item.get("category") not in ALLOWED_CATEGORY:
            fail(errors, f"{iid}: invalid category")
        if item.get("evidence_band") not in ALLOWED_BANDS:
            fail(errors, f"{iid}: invalid evidence_band")
        refs = item.get("claim_ids", [])
        if not refs:
            fail(errors, f"{iid}: intervention must reference a claim")
        for ref in refs:
            if ref not in claim_ids:
                fail(errors, f"{iid}: unknown claim {ref}")
        if not DATE_RE.match(item.get("reviewed_at", "")):
            fail(errors, f"{iid}: invalid reviewed_at")

    if errors:
        print("EVIDENCE VALIDATION: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"EVIDENCE VALIDATION: PASS — {len(interventions)} interventions, {len(claims)} claims, {len(sources)} sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
