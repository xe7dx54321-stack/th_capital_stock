"""Source evidence linkage utilities for fundamentals fields."""

from __future__ import annotations

from typing import Any


def collect_field_evidence_ids(field_details: dict[str, Any]) -> list[str]:
    evidence_ids: list[str] = []
    for detail in (field_details or {}).values():
        if detail.get("source_evidence_ids"):
            evidence_ids.extend(str(item) for item in detail.get("source_evidence_ids") or [] if item)
        elif detail.get("source_evidence_id"):
            evidence_ids.append(str(detail["source_evidence_id"]))
        if detail.get("input_evidence_ids"):
            evidence_ids.extend(str(item) for item in detail.get("input_evidence_ids") or [] if item)
    return list(dict.fromkeys(evidence_ids))


def link_field_evidence(
    field_details: dict[str, Any],
    *,
    field_source_map: dict[str, str] | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach field-level source metadata when a justified source is known.

    The helper intentionally does not invent evidence for arbitrary fields.  It
    only uses explicit per-field mappings or inherited derived-field evidence.
    """

    field_source_map = {str(k): str(v) for k, v in (field_source_map or {}).items() if v}
    source_metadata = source_metadata or {}
    linked: dict[str, Any] = {}
    for field, original in (field_details or {}).items():
        detail = dict(original or {})
        evidence_ids = [str(item) for item in detail.get("source_evidence_ids") or [] if item]
        if not evidence_ids and detail.get("source_evidence_id"):
            evidence_ids.append(str(detail["source_evidence_id"]))
        if not evidence_ids and detail.get("input_evidence_ids"):
            evidence_ids.extend(str(item) for item in detail.get("input_evidence_ids") or [] if item)
        mapped = field_source_map.get(field)
        if not evidence_ids and mapped:
            evidence_ids = [mapped]
            detail["source_evidence_id"] = mapped
            detail["source_evidence_ids"] = [mapped]
        elif evidence_ids:
            evidence_ids = list(dict.fromkeys(evidence_ids))
            detail["source_evidence_id"] = detail.get("source_evidence_id") or evidence_ids[0]
            detail["source_evidence_ids"] = evidence_ids
        detail.setdefault("source_filing_id", source_metadata.get("source_filing_id") or source_metadata.get("source_snapshot_id"))
        detail.setdefault("source_chunk_id", detail.get("chunk_id") or source_metadata.get("source_chunk_id"))
        detail.setdefault("source_section_type", detail.get("chunk_section_type") or source_metadata.get("source_section_type"))
        detail.setdefault("source_url", source_metadata.get("source_url"))
        detail.setdefault("published_at", detail.get("period") or source_metadata.get("published_at"))
        if detail.get("extracted_value") is not None and not detail.get("source_evidence_id"):
            detail["evidence_linkage_missing_reason"] = "missing_source_evidence_id"
        else:
            detail["evidence_linkage_missing_reason"] = None
        linked[field] = detail
    return linked

