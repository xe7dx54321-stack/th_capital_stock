"""Derived fundamentals helpers with evidence inheritance."""

from __future__ import annotations

from typing import Any


def _value(detail: dict[str, Any] | None) -> float | None:
    if not detail:
        return None
    value = detail.get("extracted_value")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _evidence_ids(*details: dict[str, Any] | None) -> list[str]:
    ids: list[str] = []
    for detail in details:
        if not detail:
            continue
        if detail.get("source_evidence_ids"):
            ids.extend(str(item) for item in detail.get("source_evidence_ids") or [] if item)
        elif detail.get("source_evidence_id"):
            ids.append(str(detail["source_evidence_id"]))
    return list(dict.fromkeys(ids))


def _min_confidence(*details: dict[str, Any] | None) -> float:
    values = [float((detail or {}).get("confidence") or 0.0) for detail in details]
    return min(values) if values else 0.0


def _missing_detail(field: str, formula: str, input_fields: list[str], missing_inputs: list[str]) -> dict[str, Any]:
    return {
        "field": field,
        "extracted_value": None,
        "value": None,
        "extraction_method": "derived",
        "method": "derived",
        "formula": formula,
        "input_fields": input_fields,
        "input_evidence_ids": [],
        "source_evidence_id": None,
        "source_evidence_ids": [],
        "confidence": 0.0,
        "missing_reason": "derived_field_missing_inputs",
        "missing_inputs": missing_inputs,
        "warnings": [f"missing_inputs:{','.join(missing_inputs)}"],
    }


def derive_gross_margin(field_details: dict[str, Any]) -> dict[str, Any]:
    gross_profit = field_details.get("gross_profit") or {}
    revenue = field_details.get("revenue") or {}
    missing = [field for field, detail in (("gross_profit", gross_profit), ("revenue", revenue)) if _value(detail) in (None, 0)]
    if missing:
        return _missing_detail("gross_margin", "gross_profit / revenue", ["gross_profit", "revenue"], missing)
    evidence_ids = _evidence_ids(gross_profit, revenue)
    value = float(_value(gross_profit) or 0.0) / float(_value(revenue) or 1.0)
    return {
        "field": "gross_margin",
        "extracted_value": value,
        "value": value,
        "unit": "ratio",
        "currency": gross_profit.get("currency") or revenue.get("currency"),
        "period": gross_profit.get("period") or revenue.get("period"),
        "source_evidence_id": evidence_ids[0] if evidence_ids else None,
        "source_evidence_ids": evidence_ids,
        "input_evidence_ids": evidence_ids,
        "input_fields": ["gross_profit", "revenue"],
        "confidence": round(_min_confidence(gross_profit, revenue) * 0.92, 3),
        "missing_reason": None,
        "source_text": "gross_profit / revenue",
        "chunk_id": gross_profit.get("chunk_id") or revenue.get("chunk_id"),
        "chunk_section_type": gross_profit.get("chunk_section_type") or revenue.get("chunk_section_type"),
        "source_section_type": gross_profit.get("source_section_type") or revenue.get("source_section_type"),
        "method": "derived",
        "extraction_method": "derived",
        "formula": "gross_profit / revenue",
        "warnings": [],
    }


def derive_free_cash_flow(field_details: dict[str, Any]) -> dict[str, Any]:
    operating_cash_flow = field_details.get("operating_cash_flow") or {}
    capex = field_details.get("capex") or {}
    missing = [
        field
        for field, detail in (("operating_cash_flow", operating_cash_flow), ("capex", capex))
        if _value(detail) is None
    ]
    if missing:
        return _missing_detail("free_cash_flow", "operating_cash_flow - capex", ["operating_cash_flow", "capex"], missing)
    evidence_ids = _evidence_ids(operating_cash_flow, capex)
    value = float(_value(operating_cash_flow) or 0.0) - abs(float(_value(capex) or 0.0))
    return {
        "field": "free_cash_flow",
        "extracted_value": value,
        "value": value,
        "unit": operating_cash_flow.get("unit") or capex.get("unit"),
        "currency": operating_cash_flow.get("currency") or capex.get("currency"),
        "period": operating_cash_flow.get("period") or capex.get("period"),
        "source_evidence_id": evidence_ids[0] if evidence_ids else None,
        "source_evidence_ids": evidence_ids,
        "input_evidence_ids": evidence_ids,
        "input_fields": ["operating_cash_flow", "capex"],
        "confidence": round(_min_confidence(operating_cash_flow, capex) * 0.9, 3),
        "missing_reason": None,
        "source_text": "operating_cash_flow - capex",
        "chunk_id": operating_cash_flow.get("chunk_id") or capex.get("chunk_id"),
        "chunk_section_type": operating_cash_flow.get("chunk_section_type") or capex.get("chunk_section_type"),
        "source_section_type": operating_cash_flow.get("source_section_type") or capex.get("source_section_type"),
        "method": "derived",
        "extraction_method": "derived",
        "formula": "operating_cash_flow - capex",
        "warnings": [],
    }

