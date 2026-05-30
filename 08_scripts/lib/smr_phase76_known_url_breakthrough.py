#!/usr/bin/env python3
import json
from pathlib import Path

ALLOWED_SOURCE_TYPES = [
    "exchange_announcement_page", "exchange_pdf_url", "company_ir_page",
    "company_announcement_page", "static_text_page", "known_pdf_url", "manual_research_url"
]

def validate_candidate(candidate):
    url = candidate.get("url", "").strip()
    title = candidate.get("title", "").strip()
    st = candidate.get("source_type", "")
    if not url:
        return {"valid": False, "reason": "empty_url"}
    if not title:
        return {"valid": False, "reason": "empty_title"}
    if st not in ALLOWED_SOURCE_TYPES:
        return {"valid": False, "reason": f"invalid_source_type: {st}"}
    return {"valid": True, "reason": None}

def load_candidates(ticker="300394.SZ"):
    cfg_path = Path(__file__).resolve().parents[2] / "config" / "phase76_300394_known_url_candidates.json"
    if not cfg_path.exists():
        return []
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("candidates", [])

def verify_candidates(candidates):
    verified = []
    for c in candidates:
        v = validate_candidate(c)
        c["verification_status"] = "verified" if v["valid"] else f"invalid: {v['reason']}"
        if v["valid"]:
            c["raw_save_allowed"] = False
            c["ocr_allowed"] = False
            c["allowed_usage"] = c.get("allowed_usage", "business_context")
        verified.append(c)
    return verified
