from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PACKET_SCHEMA_VERSION = "2.0"
CORE_FUNDAMENTAL_FIELDS = ("revenue", "net_income", "operating_cash_flow", "gross_margin", "roe")


def build_stock_research_packet(
    *,
    ticker: str,
    market: str,
    normalized: dict[str, Any],
) -> dict[str, Any]:
    fundamentals = normalized["fundamentals"]
    valuation = normalized["valuation"]
    evidence = normalized["evidence"]
    risk = normalized["risk"]
    evidence_ids = set(evidence.get("usable_evidence_ids") or [])
    issues = [
        *(fundamentals.get("issues") or []),
        *(valuation.get("issues") or []),
        *(evidence.get("issues") or []),
    ]
    quarantined_paths = [
        *(f"fundamentals.{name}" for name in fundamentals.get("quarantined_fields") or []),
        *(f"valuation.{name}" for name in valuation.get("quarantined_fields") or []),
    ]

    evidence_closure_failures = []
    for dataset_name, dataset in (("fundamentals", fundamentals), ("valuation", valuation)):
        for field_name, field in (dataset.get("fields") or {}).items():
            if field.get("status") != "valid":
                continue
            unknown = [value for value in field.get("evidence_ids") or [] if value not in evidence_ids]
            if unknown:
                field["status"] = "quarantined"
                field.setdefault("reasons", []).append("evidence_not_in_packet")
                path = f"{dataset_name}.{field_name}"
                quarantined_paths.append(path)
                evidence_closure_failures.append({"path": path, "unknown_evidence_ids": unknown})
    if evidence_closure_failures:
        issues.append({
            "code": "evidence_closure_failed",
            "severity": "blocker",
            "fields": [item["path"] for item in evidence_closure_failures],
        })

    valid_core_fields = [
        name
        for name in CORE_FUNDAMENTAL_FIELDS
        if (fundamentals.get("fields") or {}).get(name, {}).get("status") == "valid"
    ]
    freshness = risk.get("freshness") or {}
    freshness_blocked = str(freshness.get("blocking_level") or "").lower() in {"block", "blocker", "critical"}
    blockers = [issue["code"] for issue in issues if issue.get("severity") == "blocker"]
    if not evidence_ids:
        blockers.append("no_usable_evidence")
    if freshness_blocked:
        blockers.append("market_data_blocked")
    blockers = list(dict.fromkeys(blockers))

    if not evidence_ids:
        readiness = "cannot_conclude"
    elif len(valid_core_fields) >= 2 and not blockers:
        readiness = "research_ready"
    else:
        readiness = "evidence_limited"

    gaps = []
    for name in CORE_FUNDAMENTAL_FIELDS:
        field = (fundamentals.get("fields") or {}).get(name) or {"status": "missing", "reasons": ["field_missing"]}
        if field.get("status") != "valid":
            gaps.append({"path": f"fundamentals.{name}", "status": field.get("status"), "reasons": field.get("reasons") or []})
    if not any(field.get("status") == "valid" for field in (valuation.get("fields") or {}).values()):
        gaps.append({"path": "valuation", "status": valuation.get("status"), "reasons": ["no_cited_valuation_fields"]})

    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "ticker": ticker,
        "market": market,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "identity": {"ticker": ticker, "market": market},
        "datasets": {
            "fundamentals": fundamentals,
            "valuation": valuation,
            "evidence": evidence,
            "risk": risk,
            "market": {"status": "not_loaded", "observations": []},
        },
        "quality": {
            "readiness": readiness,
            "issues": issues,
            "blockers": blockers,
            "usable_evidence_ids": sorted(evidence_ids),
            "valid_core_fundamental_fields": valid_core_fields,
            "quarantined_fields": sorted(set(quarantined_paths)),
            "evidence_closure_failures": evidence_closure_failures,
        },
        "claims": [],
        "scenarios": [],
        "evidence_gaps": gaps,
    }
