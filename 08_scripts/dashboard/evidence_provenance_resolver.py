"""Evidence and Provenance Resolver for the SMR Dashboard.

Enriches data items with standardized provenance fields and
assesses provenance confidence levels. Items with
provenance_confidence = none must not enter the main signal flow.

Important: This is a read-only resolver. It does not write state,
does not access networks, does not read secrets, and does not
create data artifacts.
"""

from __future__ import annotations

from typing import Any


EVIDENCE_KEYS = [
    "source_url",
    "original_url",
    "report_path",
    "evidence_packet_id",
    "evidence_id",
    "filing_url",
    "pdf_path",
    "source_rel_path",
    "source_refs",
    "evidence_url",
    "document_path",
    "source_doc",
]

SOURCE_KEYS = [
    "source_name",
    "source_type",
    "source_label",
    "provider",
    "org_name",
    "source_kind",
    "source_category",
]

TIMESTAMP_KEYS = [
    "published_at",
    "observed_at",
    "generated_at",
    "created_at",
    "alert_time",
    "event_time",
    "trade_date",
    "publish_time",
    "report_date",
    "updated_at",
]

ENTITY_KEYS = [
    "entity",
    "entity_name",
    "company_name",
    "stock_name",
    "topic",
    "industry",
    "symbol",
    "ticker",
]


def _extract_first_value(item: dict[str, Any], keys: list[str]) -> str | None:
    """Extract the first non-empty value from a list of keys."""
    for key in keys:
        value = item.get(key)
        if value:
            if isinstance(value, list):
                if any(v for v in value if v):
                    return str(value[0])
            elif isinstance(value, str) and value.strip():
                return value.strip()
            elif isinstance(value, (int, float)):
                return str(value)
    return None


def _extract_evidence(item: dict[str, Any]) -> dict[str, Any]:
    """Extract evidence-related fields from an item."""
    result = {
        "source_url": None,
        "report_path": None,
        "evidence_id": None,
        "evidence_packet_id": None,
        "has_evidence": False,
    }

    for key in EVIDENCE_KEYS:
        value = item.get(key)
        if value:
            if isinstance(value, list):
                if any(v for v in value if v):
                    result["has_evidence"] = True
            elif isinstance(value, str) and value.strip():
                result["has_evidence"] = True
            if key in ("source_url", "original_url", "evidence_url", "filing_url"):
                result["source_url"] = str(value) if not isinstance(value, list) else str(value[0])
            elif key in ("report_path", "pdf_path", "document_path", "source_doc", "source_rel_path"):
                result["report_path"] = str(value) if not isinstance(value, list) else str(value[0])
            elif key in ("evidence_packet_id", "evidence_id", "source_refs"):
                if key == "evidence_packet_id":
                    result["evidence_packet_id"] = str(value) if not isinstance(value, list) else str(value[0])
                else:
                    result["evidence_id"] = str(value) if not isinstance(value, list) else str(value[0])

    return result


def _extract_source_info(item: dict[str, Any]) -> dict[str, Any]:
    """Extract source-related fields from an item."""
    result = {
        "source_type": None,
        "source_name": None,
        "has_source": False,
    }

    for key in SOURCE_KEYS:
        value = item.get(key)
        if value:
            if isinstance(value, str) and value.strip():
                result["has_source"] = True
            if key == "source_type" and value:
                result["source_type"] = str(value)
            elif key in ("source_name", "source_label", "provider", "org_name") and value:
                result["source_name"] = str(value)

    return result


def _extract_timestamp(item: dict[str, Any]) -> dict[str, Any]:
    """Extract timestamp fields from an item."""
    result = {
        "published_at": None,
        "observed_at": None,
        "generated_at": None,
        "has_timestamp": False,
    }

    for key in TIMESTAMP_KEYS:
        value = item.get(key)
        if value:
            if isinstance(value, str) and value.strip():
                result["has_timestamp"] = True
            if key in ("published_at", "publish_time") and value:
                result["published_at"] = str(value)
            elif key in ("observed_at", "event_time", "alert_time", "trade_date") and value:
                result["observed_at"] = str(value)
            elif key in ("generated_at", "created_at", "updated_at", "report_date") and value:
                result["generated_at"] = str(value)

    return result


def _extract_entity(item: dict[str, Any]) -> dict[str, Any]:
    """Extract entity-related fields from an item."""
    entity = _extract_first_value(item, ENTITY_KEYS)
    return {
        "entity": entity,
        "has_entity": entity is not None,
    }


def assess_provenance_confidence(
    has_evidence: bool,
    has_source: bool,
    has_timestamp: bool,
    is_generated_summary: bool = False,
    is_default_fallback: bool = False,
    is_placeholder: bool = False,
) -> str:
    """Assess provenance confidence level.

    Returns:
        'high', 'medium', 'low', or 'none'
    """
    if is_placeholder or is_default_fallback:
        return "none"

    if is_generated_summary:
        return "none"

    if has_evidence and has_source and has_timestamp:
        return "high"

    if has_source and (has_evidence or has_timestamp):
        return "medium"

    if has_source or has_timestamp:
        return "low"

    return "none"


def resolve_provenance(item: dict[str, Any]) -> dict[str, Any]:
    """Resolve and enrich provenance information for a data item.

    Takes a raw data item and returns a dict with standardized
    provenance fields and confidence assessment.

    Args:
        item: Raw data item dict.

    Returns:
        Dict with provenance fields and confidence level.
    """
    evidence = _extract_evidence(item)
    source = _extract_source_info(item)
    timestamp = _extract_timestamp(item)
    entity = _extract_entity(item)

    is_generated = bool(item.get("is_generated_summary") or item.get("generated_summary"))
    is_fallback = bool(item.get("is_default_fallback") or item.get("default_fallback"))
    is_placeholder = bool(item.get("is_placeholder") or item.get("placeholder"))

    data_status = str(item.get("data_status") or "")
    if data_status in ("placeholder", "default", "default_fallback"):
        is_fallback = data_status == "default_fallback" or data_status == "default"
        is_placeholder = data_status == "placeholder"

    truth_status = str(item.get("truth_status") or "")
    if truth_status == "generated_summary":
        is_generated = True
    elif truth_status == "default_fallback":
        is_fallback = True
    elif truth_status == "placeholder":
        is_placeholder = True

    confidence = assess_provenance_confidence(
        has_evidence=evidence["has_evidence"],
        has_source=source["has_source"],
        has_timestamp=timestamp["has_timestamp"],
        is_generated_summary=is_generated,
        is_default_fallback=is_fallback,
        is_placeholder=is_placeholder,
    )

    return {
        "source_type": source["source_type"] or item.get("source_type"),
        "source_name": source["source_name"] or item.get("source_name"),
        "source_url": evidence["source_url"] or item.get("source_url"),
        "report_path": evidence["report_path"] or item.get("report_path"),
        "evidence_id": evidence["evidence_id"] or item.get("evidence_id"),
        "evidence_packet_id": evidence["evidence_packet_id"] or item.get("evidence_packet_id"),
        "published_at": timestamp["published_at"] or item.get("published_at"),
        "observed_at": timestamp["observed_at"] or item.get("observed_at"),
        "generated_at": timestamp["generated_at"] or item.get("generated_at"),
        "entity": entity["entity"] or item.get("entity"),
        "truth_status": truth_status or item.get("truth_status") or "",
        "data_status": data_status or item.get("data_status") or "",
        "provenance_confidence": confidence,
        "has_source": source["has_source"],
        "has_evidence_packet": evidence["has_evidence"],
        "has_timestamp": timestamp["has_timestamp"],
        "is_generated_summary": is_generated,
        "is_default_fallback": is_fallback,
        "is_placeholder": is_placeholder,
        "can_enter_main_flow": confidence in ("high", "medium"),
    }


def enrich_with_provenance(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich a list of items with provenance information.

    Args:
        items: List of raw data item dicts.

    Returns:
        List of enriched items with provenance fields added.
    """
    enriched = []
    for item in items:
        provenance = resolve_provenance(item)
        enriched_item = dict(item)
        enriched_item.update(provenance)
        enriched.append(enriched_item)
    return enriched


def filter_main_flow_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter items to only those that can enter the main signal flow.

    Args:
        items: List of data item dicts.

    Returns:
        List of items with provenance_confidence high or medium.
    """
    enriched = enrich_with_provenance(items)
    return [item for item in enriched if item.get("can_enter_main_flow")]


def summarize_provenance(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a provenance summary for a list of items.

    Args:
        items: List of data item dicts.

    Returns:
        Dict with counts by provenance confidence level.
    """
    enriched = enrich_with_provenance(items)

    high_count = sum(1 for item in enriched if item.get("provenance_confidence") == "high")
    medium_count = sum(1 for item in enriched if item.get("provenance_confidence") == "medium")
    low_count = sum(1 for item in enriched if item.get("provenance_confidence") == "low")
    none_count = sum(1 for item in enriched if item.get("provenance_confidence") == "none")

    evidence_backed = sum(1 for item in enriched if item.get("has_evidence_packet"))
    source_backed = sum(1 for item in enriched if item.get("has_source"))
    generated = sum(1 for item in enriched if item.get("is_generated_summary"))
    fallback = sum(1 for item in enriched if item.get("is_default_fallback"))
    placeholder = sum(1 for item in enriched if item.get("is_placeholder"))

    main_flow_count = high_count + medium_count
    filtered_count = none_count

    return {
        "total_count": len(enriched),
        "high_confidence_count": high_count,
        "medium_confidence_count": medium_count,
        "low_confidence_count": low_count,
        "none_confidence_count": none_count,
        "evidence_backed_count": evidence_backed,
        "source_backed_count": source_backed,
        "generated_summary_count": generated,
        "default_fallback_count": fallback,
        "placeholder_count": placeholder,
        "main_flow_eligible_count": main_flow_count,
        "filtered_out_count": filtered_count,
    }
