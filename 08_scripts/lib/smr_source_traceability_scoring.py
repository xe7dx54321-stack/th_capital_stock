#!/usr/bin/env python3
"""Phase 51 source traceability scoring."""
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

def score_traceability(candidate):
    checks = {"source_id_present": bool(candidate.get("source_id")),
              "source_url_present": bool(candidate.get("source_url", "")),
              "source_date_present": bool(candidate.get("source_date", "")),
              "source_provider_present": bool(candidate.get("source_provider", "")),
              "source_type_known": candidate.get("source_type", "unknown") != "unknown",
              "chunk_id_present": bool(candidate.get("chunk_id")),
              "normalized_text_id_present": bool(candidate.get("normalized_text_id")),
              "quoted_span_linked": bool(candidate.get("quoted_span"))}
    score = sum(1 for v in checks.values() if v) / max(len(checks), 1)
    penalties = []
    # fixture penalty
    sid = candidate.get("source_id") or ""
    if "fixture" in sid.lower() or "cninfo" in sid:
        penalties.append("fixture_penalty"); score = max(0.2, score - 0.15)
    # missing core fields penalty
    if not candidate.get("source_id"): score = max(0.1, score - 0.3)
    if not candidate.get("chunk_id"): score = max(0.1, score - 0.3)
    if score >= 0.7: bucket = "high"
    elif score >= 0.4: bucket = "medium"
    else: bucket = "low"
    return {"candidate_id": candidate.get("candidate_id"), "traceability_score": round(score, 2),
            "traceability_bucket": bucket, **checks, "penalties": penalties}

def build_traceability_report(candidates, ticker=TARGET_REVIEW_TICKER):
    rows = [score_traceability(c) for c in candidates]
    avg = sum(r["traceability_score"] for r in rows) / max(len(rows), 1)
    return {"ticker": normalize_ticker(ticker), "source_traceability_score": {
        "candidates_checked": len(candidates),
        "traceability_high": sum(1 for r in rows if r["traceability_bucket"] == "high"),
        "traceability_medium": sum(1 for r in rows if r["traceability_bucket"] == "medium"),
        "traceability_low": sum(1 for r in rows if r["traceability_bucket"] == "low"),
        "average_traceability_score": round(avg, 2), "rows": rows
    }}
