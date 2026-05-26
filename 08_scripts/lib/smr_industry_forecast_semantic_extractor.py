#!/usr/bin/env python3
"""Phase 27 industry forecast semantic extraction."""

from __future__ import annotations

from typing import Any

from smr_ir_source_inventory import MOCK_INDUSTRY_SOURCES
from smr_semantic_document_chunker import chunk_sources


def build_industry_forecast_evidence(theme: str = "ai_optical_interconnect", *, mode: str = "mock") -> dict[str, Any]:
    if mode == "llm":
        return {"theme": theme, "industry_forecast_evidence": [], "llm_enabled": False, "message": "LLM mode reserved; mock is default."}
    chunks = chunk_sources(MOCK_INDUSTRY_SOURCES)
    rows = []
    for chunk in chunks:
        text = chunk.get("text") or ""
        if "800G" not in text and "光模块" not in text:
            continue
        quoted = text
        rows.append(
            {
                "source_id": chunk.get("source_id"),
                "chunk_id": chunk.get("chunk_id"),
                "forecast_object": "800G optical modules",
                "forecast_metric": "demand_growth",
                "forecast_period": "2025-2026" if "2025-2026" in text else "unknown",
                "forecast_direction": "positive" if "增长" in text else "unknown",
                "source_quality": "public_industry_commentary",
                "confidence": "medium",
                "quoted_span": quoted,
                "limitations": ["not company-specific", "public summary, not full paid report"],
                "allowed_usage": "end_demand_proxy",
            }
        )
    return {
        "theme": theme,
        "industry_forecast_evidence": rows,
        "summary": {
            "forecast_items": len(rows),
            "planned_paid_source_used": False,
            "company_specific_orders_claimed": 0,
        },
    }
