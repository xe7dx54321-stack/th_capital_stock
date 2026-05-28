#!/usr/bin/env python3
"""Phase 51 chunk quality classifier."""
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

HIGH_SIGNAL_TYPES = {"qa_section", "order_visibility_commentary", "shipment_delivery_commentary"}
USABLE_TYPES = {"product_business_description", "management_commentary", "financial_section"}
GENERIC_TYPES = {"general_text", "risk_section"}

def classify_chunk(chunk):
    ctype = chunk.get("chunk_type", "unknown")
    if ctype in HIGH_SIGNAL_TYPES: bucket = "high_signal_chunk"
    elif ctype in USABLE_TYPES: bucket = "usable_tracking_chunk"
    elif ctype in GENERIC_TYPES: bucket = "generic_context_chunk"
    elif ctype == "unknown": bucket = "generic_context_chunk"
    else: bucket = "usable_tracking_chunk"
    if chunk.get("text_chars", 0) < 20: bucket = "too_short_chunk"
    allow = bucket not in ("too_short_chunk", "title_only_chunk")
    return {"chunk_id": chunk.get("chunk_id"), "chunk_type": ctype,
            "quality_bucket": bucket, "linked_variables": _map_vars(chunk),
            "candidate_generation_allowed": allow,
            "text_chars": chunk.get("text_chars", 0)}

def _map_vars(chunk):
    text = (chunk.get("content", "") or "").lower()
    mapping = {"产品": "product_mix", "订单": "order_visibility", "出货": "shipment",
               "利润": "margin_signal", "客户": "customer_allocation_proxy"}
    return sorted(set(v for k, v in mapping.items() if k in text))

def build_chunk_quality(chunks, ticker=TARGET_REVIEW_TICKER):
    rows = [classify_chunk(c) for c in chunks]
    buckets = {}
    for r in rows: buckets[r["quality_bucket"]] = buckets.get(r["quality_bucket"], 0) + 1
    return {"ticker": normalize_ticker(ticker), "chunk_quality_report": {
        "chunks_checked": len(chunks),
        "high_signal_chunks": buckets.get("high_signal_chunk", 0),
        "usable_tracking_chunks": buckets.get("usable_tracking_chunk", 0),
        "generic_context_chunks": buckets.get("generic_context_chunk", 0),
        "unusable_chunks": buckets.get("too_short_chunk", 0) + buckets.get("title_only_chunk", 0),
        "rows": rows
    }}
