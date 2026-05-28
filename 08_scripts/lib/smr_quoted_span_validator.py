#!/usr/bin/env python3
"""Phase 51 quoted span validator — validate evidence span quality."""
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

TITLE_PATTERNS = ["公告", "报告", "预告", "关于", "年报", "季报", "半年报"]
BOILERPLATE = ["风险提示", "免责声明", "以上内容", "仅供参考", "投资有风险"]

def validate_span(candidate):
    span = candidate.get("quoted_span", "") or ""
    passed = []; failed = []
    if span: passed.append("span_present")
    else: failed.append("span_present")
    if len(span) >= 30: passed.append("span_min_length")
    else: failed.append("span_min_length")
    if candidate.get("chunk_id"): passed.append("span_from_chunk")
    else: failed.append("span_from_chunk")
    # title-only detection
    is_title = any(span.strip().startswith(p) for p in TITLE_PATTERNS) and len(span) < 40
    if not is_title: passed.append("span_not_title_only")
    else: failed.append("span_not_title_only")
    # boilerplate
    is_boiler = any(bp in span for bp in BOILERPLATE)
    if not is_boiler: passed.append("span_not_generic_boilerplate")
    else: failed.append("span_not_generic_boilerplate")
    if candidate.get("source_id"): passed.append("span_traceable_to_source")
    else: failed.append("span_traceable_to_source")
    # variable signal
    if candidate.get("variable"): passed.append("span_has_variable_signal")
    else: failed.append("span_has_variable_signal")

    score = len(passed) / max(len(passed) + len(failed), 1)
    if len(failed) == 0: status = "passed"
    elif len(failed) <= 2: status = "downgraded"
    else: status = "rejected"

    return {"candidate_id": candidate.get("candidate_id"), "span_status": status,
            "span_score": round(score, 2), "validation_passed": passed, "validation_failed": failed}

def build_span_report(candidates, ticker=TARGET_REVIEW_TICKER):
    rows = [validate_span(c) for c in candidates]
    return {"ticker": normalize_ticker(ticker), "quoted_span_validation": {
        "candidates_checked": len(candidates),
        "span_passed": sum(1 for r in rows if r["span_status"] == "passed"),
        "span_downgraded": sum(1 for r in rows if r["span_status"] == "downgraded"),
        "span_rejected": sum(1 for r in rows if r["span_status"] == "rejected"),
        "rows": rows
    }}
