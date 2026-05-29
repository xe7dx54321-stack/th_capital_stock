#!/usr/bin/env python3
"""Phase 67b evidence claim mapper."""
from smr_deep_evidence_claim_mapper import map_evidence_to_claims
def map_67b_claims(evidence_rows:list[dict])->dict:
    return map_evidence_to_claims(evidence_rows)
