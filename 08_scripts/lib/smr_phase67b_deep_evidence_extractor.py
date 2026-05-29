#!/usr/bin/env python3
"""Phase 67b deep evidence extractor - wrapper for Phase 66 extractor."""
from typing import Any
from smr_deep_business_evidence_extractor import extract_deep_evidence, BUSINESS_VARIABLES, EVIDENCE_STRENGTHS
def run_67b_extraction(texts:list[dict])->dict[str,Any]:
    return extract_deep_evidence(texts)
