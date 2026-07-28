from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


AMOUNT_FIELDS = (
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "capex",
    "free_cash_flow",
    "cash_and_equivalents",
    "total_debt",
    "shareholders_equity",
)
PER_SHARE_FIELDS = ("eps_basic", "eps_diluted")
RATIO_FIELDS = ("gross_margin", "operating_margin", "net_margin", "roe", "roic")
FUNDAMENTAL_FIELDS = (*AMOUNT_FIELDS, *PER_SHARE_FIELDS, *RATIO_FIELDS)
DERIVED_FIELD_DEPENDENCIES = {
    "gross_margin": ("gross_profit", "revenue"),
    "operating_margin": ("operating_income", "revenue"),
    "net_margin": ("net_income", "revenue"),
    "roe": ("net_income", "shareholders_equity"),
    "roic": ("operating_income", "total_debt", "shareholders_equity"),
}
VALUATION_RANGES = {
    "current_price": (0.0, 1_000_000.0),
    "market_cap": (0.0, 1e18),
    "pe_ttm": (0.0, 300.0),
    "ps_ttm": (0.0, 100.0),
    "pb": (0.0, 100.0),
    "ev_ebitda_ttm": (0.0, 500.0),
}
USAGE_ALLOWED_FOR_CLAIMS = {"research", "analysis", "promotion_evidence", "supporting_evidence"}
UNIT_MULTIPLIERS = {
    "ten_thousand": 1e4,
    "hundred_million": 1e8,
    "million": 1e6,
    "billion": 1e9,
}


def _number(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _unique_strings(values: Any) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return []
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _default_currency(market: str) -> str:
    return {"A": "CNY", "H": "HKD", "US": "USD"}.get(market, "UNKNOWN")


def _raw_amount_matches_detail(value: float, detail: dict[str, Any]) -> bool | None:
    raw_value = _number(detail.get("raw_value"))
    if raw_value is None:
        return None
    unit = str(detail.get("unit") or "").strip().lower()
    multiplier = 1.0
    for label, candidate in UNIT_MULTIPLIERS.items():
        if unit.startswith(label + " "):
            multiplier = candidate
            break
    expected = raw_value * multiplier
    tolerance = max(abs(value), abs(expected), 1.0) * 0.01
    return abs(value - expected) <= tolerance


def _field_evidence(snapshot: dict[str, Any], field: str) -> list[str]:
    detail = (snapshot.get("field_details") or {}).get(field) or {}
    return _unique_strings(
        detail.get("source_evidence_ids")
        or detail.get("evidence_ids")
        or detail.get("source_evidence_id")
        or snapshot.get("source_evidence_ids")
    )


def _quarantine(field: dict[str, Any], reason: str) -> None:
    if field["status"] == "missing":
        return
    field["status"] = "quarantined"
    if reason not in field["reasons"]:
        field["reasons"].append(reason)


def normalize_fundamentals(snapshot: dict[str, Any] | None, market: str) -> dict[str, Any]:
    raw = dict(snapshot or {})
    if not raw:
        return {
            "status": "missing",
            "period": None,
            "fields": {},
            "issues": [{"code": "fundamentals_missing", "severity": "blocker", "fields": []}],
            "source_quality": None,
            "freshness_status": "missing",
        }

    top_level_period = str(raw.get("period") or "").strip() or None
    period_counts: dict[str, int] = {}
    for name in FUNDAMENTAL_FIELDS:
        if _number(raw.get(name)) is None:
            continue
        detail_period = str(((raw.get("field_details") or {}).get(name) or {}).get("period") or "").strip()
        if detail_period:
            period_counts[detail_period] = period_counts.get(detail_period, 0) + 1
    inferred_period = (
        sorted(period_counts, key=lambda value: (-period_counts[value], value))[0]
        if period_counts
        else None
    )
    period = top_level_period or inferred_period
    currency = str((raw.get("metadata") or {}).get("currency") or _default_currency(market))
    fields: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []

    for name in FUNDAMENTAL_FIELDS:
        value = _number(raw.get(name))
        detail = (raw.get("field_details") or {}).get(name) or {}
        field_period = str(detail.get("period") or period or "").strip() or None
        evidence_ids = _field_evidence(raw, name)
        unit = "ratio" if name in RATIO_FIELDS else f"{currency}/share" if name in PER_SHARE_FIELDS else currency
        field = {
            "value": value,
            "raw_value": raw.get(name),
            "unit": unit,
            "period": field_period,
            "evidence_ids": evidence_ids,
            "confidence": _number(detail.get("confidence") if detail else raw.get("confidence")),
            "allowed_usage": detail.get("allowed_usage") or "research",
            "status": "valid" if value is not None else "missing",
            "reasons": [],
            "comparison": None,
            "expectation": None,
        }
        if value is None:
            field["reasons"].append(
                detail.get("missing_reason")
                or (raw.get("field_missing_reasons") or {}).get(name)
                or "field_missing"
            )
        elif name in RATIO_FIELDS:
            if abs(value) > 1 and abs(value) <= 100:
                field["value"] = value / 100
                field["reasons"].append("percent_normalized_to_ratio")
            normalized = field["value"]
            lower, upper = (-1.0, 1.0) if name.endswith("margin") else (-5.0, 5.0)
            if normalized is None or not lower <= normalized <= upper:
                _quarantine(field, "ratio_out_of_range")
        elif name in PER_SHARE_FIELDS and abs(value) > 1_000:
            _quarantine(field, "per_share_value_out_of_range")
        elif name in AMOUNT_FIELDS and abs(value) > 1e18:
            _quarantine(field, "amount_out_of_range")

        normalized_unit = str(detail.get("normalized_unit") or "").upper()
        if name in AMOUNT_FIELDS and normalized_unit in {"CNY", "HKD", "USD"} and normalized_unit != currency.upper():
            _quarantine(field, "currency_unit_mismatch")
        if name in AMOUNT_FIELDS and value is not None:
            raw_match = _raw_amount_matches_detail(value, detail)
            if raw_match is False:
                _quarantine(field, "raw_normalized_value_mismatch")
            elif raw_match is None and bool(detail.get("unit_inferred")):
                _quarantine(field, "unverified_amount_scale")

        if value is not None and not field_period:
            _quarantine(field, "missing_report_period")
        if value is not None and not evidence_ids:
            _quarantine(field, "missing_field_evidence")
        if str(field["allowed_usage"]).lower() not in USAGE_ALLOWED_FOR_CLAIMS:
            _quarantine(field, "usage_not_allowed")

        previous_value = _number(detail.get("previous_value") if detail else None)
        previous_period = str(detail.get("previous_period") or "").strip() if detail else ""
        if name in RATIO_FIELDS and previous_value is not None and 1 < abs(previous_value) <= 100:
            previous_value /= 100
        if value is not None and previous_value is not None and previous_period:
            change_rate = None if previous_value == 0 else (field["value"] - previous_value) / abs(previous_value)
            field["comparison"] = {
                "previous_value": previous_value,
                "previous_period": previous_period,
                "change_rate": change_rate,
                "absolute_change": field["value"] - previous_value,
            }
        expected_raw = None
        if detail:
            expected_raw = detail.get("consensus_value")
            if expected_raw is None:
                expected_raw = detail.get("expected_value")
        expected_value = _number(expected_raw)
        if name in RATIO_FIELDS and expected_value is not None and 1 < abs(expected_value) <= 100:
            expected_value /= 100
        if value is not None and expected_value is not None:
            delta_rate = None if expected_value == 0 else (field["value"] - expected_value) / abs(expected_value)
            field["expectation"] = {
                "expected_value": expected_value,
                "delta_rate": delta_rate,
            }
        fields[name] = field

    def valid_value(name: str) -> float | None:
        field = fields[name]
        return field["value"] if field["status"] == "valid" else None

    revenue = valid_value("revenue")
    gross_profit = valid_value("gross_profit")
    net_income = valid_value("net_income")
    if revenue is not None and revenue <= 0:
        _quarantine(fields["revenue"], "non_positive_revenue")
        issues.append({"code": "non_positive_revenue", "severity": "blocker", "fields": ["revenue"]})
    if revenue and gross_profit is not None and not (-0.5 * revenue <= gross_profit <= 1.2 * revenue):
        _quarantine(fields["gross_profit"], "gross_profit_revenue_conflict")
        _quarantine(fields["gross_margin"], "gross_profit_revenue_conflict")
        issues.append({
            "code": "gross_profit_revenue_conflict",
            "severity": "blocker",
            "fields": ["gross_profit", "gross_margin"],
        })
    if revenue and net_income is not None and abs(net_income) > 1.2 * revenue:
        _quarantine(fields["net_income"], "net_income_revenue_conflict")
        _quarantine(fields["net_margin"], "net_income_revenue_conflict")
        issues.append({
            "code": "net_income_revenue_conflict",
            "severity": "blocker",
            "fields": ["net_income", "net_margin"],
        })
    if revenue:
        for name in (
            "gross_profit", "operating_income", "net_income", "capex",
            "operating_cash_flow", "cash_and_equivalents", "total_debt", "shareholders_equity",
        ):
            field = fields[name]
            value = field.get("value")
            if field["status"] != "valid" or value in (None, 0):
                continue
            if abs(value) < abs(revenue) * 1e-4 or abs(value) > abs(revenue) * 100:
                _quarantine(field, "amount_scale_conflict")

    eps_basic = fields["eps_basic"]
    eps_diluted = fields["eps_diluted"]
    if eps_basic.get("value") is not None and eps_diluted.get("value") is not None:
        denominator = max(abs(eps_basic["value"]), abs(eps_diluted["value"]), 1e-9)
        if (
            eps_basic.get("period") != eps_diluted.get("period")
            or abs(eps_basic["value"] - eps_diluted["value"]) / denominator > 0.5
        ):
            _quarantine(eps_basic, "eps_cross_field_conflict")
            _quarantine(eps_diluted, "eps_cross_field_conflict")
    normalized_revenue = fields["revenue"]["value"] if fields["revenue"]["status"] == "valid" else None
    normalized_gross_profit = fields["gross_profit"]["value"] if fields["gross_profit"]["status"] == "valid" else None
    normalized_margin = fields["gross_margin"]["value"] if fields["gross_margin"]["status"] == "valid" else None
    if normalized_revenue and normalized_gross_profit is not None and normalized_margin is not None:
        derived_margin = normalized_gross_profit / normalized_revenue
        if abs(derived_margin - normalized_margin) > 0.15:
            _quarantine(fields["gross_margin"], "gross_margin_cross_field_conflict")
            issues.append({
                "code": "gross_margin_cross_field_conflict",
                "severity": "warning",
                "fields": ["gross_margin"],
            })

    for name, field in fields.items():
        detail = (raw.get("field_details") or {}).get(name) or {}
        dependencies = [
            str(value)
            for value in (detail.get("input_fields") or DERIVED_FIELD_DEPENDENCIES.get(name, ()))
        ]
        if detail.get("method") == "derived" and any(
            dependency in fields and fields[dependency]["status"] != "valid"
            for dependency in dependencies
        ):
            _quarantine(field, "derived_from_quarantined_field")

    if not period:
        issues.append({"code": "missing_report_period", "severity": "blocker", "fields": list(FUNDAMENTAL_FIELDS)})
    elif not top_level_period:
        issues.append({
            "code": "report_period_inferred_from_field_provenance",
            "severity": "warning",
            "fields": [name for name, field in fields.items() if field.get("period")],
        })
    quarantined = [name for name, field in fields.items() if field["status"] == "quarantined"]
    valid = [name for name, field in fields.items() if field["status"] == "valid"]
    status = "valid" if valid and not quarantined else "partial" if valid else "quarantined"
    return {
        "status": status,
        "period": period,
        "fields": fields,
        "issues": issues,
        "valid_fields": valid,
        "quarantined_fields": quarantined,
        "source_quality": raw.get("source_quality"),
        "freshness_status": raw.get("freshness_status") or "unknown",
        "snapshot_id": raw.get("snapshot_id"),
        "created_at": raw.get("created_at"),
    }


def normalize_valuation(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(snapshot or {})
    if not raw:
        return {"status": "missing", "as_of": None, "fields": {}, "issues": []}
    as_of = raw.get("generated_at")
    evidence_ids = _unique_strings(
        raw.get("source_evidence_ids") or (raw.get("metadata") or {}).get("source_evidence_ids")
    )
    allowed_usage = str(raw.get("allowed_usage") or "unknown").lower()
    fields: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []
    for name, (lower, upper) in VALUATION_RANGES.items():
        value = _number(raw.get(name))
        field = {
            "value": value,
            "raw_value": raw.get(name),
            "unit": "multiple" if name not in {"current_price", "market_cap"} else "currency",
            "as_of": as_of,
            "evidence_ids": evidence_ids,
            "status": "valid" if value is not None else "missing",
            "reasons": [],
        }
        if value is None:
            field["reasons"].append("field_missing")
        elif not lower < value <= upper:
            _quarantine(field, "valuation_out_of_range")
        if value is not None and not as_of:
            _quarantine(field, "missing_valuation_date")
        if value is not None and not evidence_ids:
            _quarantine(field, "missing_valuation_evidence")
        if value is not None and allowed_usage not in {"research", "analysis"}:
            _quarantine(field, "usage_not_allowed")
        fields[name] = field
    quarantined = [name for name, field in fields.items() if field["status"] == "quarantined"]
    valid = [name for name, field in fields.items() if field["status"] == "valid"]
    if quarantined:
        issues.append({"code": "valuation_fields_quarantined", "severity": "warning", "fields": quarantined})
    status = "valid" if valid and not quarantined else "partial" if valid else "quarantined"
    return {
        "status": status,
        "as_of": as_of,
        "fields": fields,
        "issues": issues,
        "valid_fields": valid,
        "quarantined_fields": quarantined,
        "allowed_usage": allowed_usage,
        "confidence": _number(raw.get("valuation_confidence")),
    }


def normalize_evidence(evidence: dict[str, Any] | None) -> dict[str, Any]:
    items = []
    issues = []
    for raw in (evidence or {}).get("items") or []:
        evidence_id = str(raw.get("evidence_id") or "").strip()
        score = _number(raw.get("quality_score")) or 0.0
        active = str(raw.get("source_status") or "active").lower() not in {"rejected", "archived", "inactive"}
        source_type = str(raw.get("source_type") or "").lower()
        source_quality = str(raw.get("source_quality") or "").lower()
        derived_snapshot = source_type in {"fundamentals", "valuation"}
        primary_filing = source_type in {"filing", "official_filing", "annual_report"} and source_quality in {"primary", "official"}
        governed_market = (
            source_type in {
                "official_exchange_daily_bars", "official_exchange_realtime_quote",
                "secondary_market_daily_bars", "secondary_realtime_quote", "secondary_valuation_quote",
                "secondary_market_quote", "secondary_valuation_history",
                "cross_validated_peer_market_matrix",
            }
            and source_quality in {"official", "reputable_secondary"}
            and str((raw.get("metadata") or {}).get("claim_category") or "")
            in {"official_market_history", "official_realtime_quote", "secondary_market_history",
                "secondary_realtime_quote", "cross_validated_valuation", "peer_comparison_matrix"}
        )
        has_source_date = bool(str(raw.get("published_at") or "").strip())
        usable = (
            bool(raw.get("usable_for_core_claim"))
            and active
            and score >= 0.6
            and bool(evidence_id)
            and has_source_date
            and not derived_snapshot
            and (primary_filing or governed_market)
        )
        item = {
            "evidence_id": evidence_id or None,
            "source_key": raw.get("source_key"),
            "source_type": raw.get("source_type"),
            "source_quality": raw.get("source_quality"),
            "published_at": raw.get("published_at"),
            "url_or_doc_id": raw.get("url_or_doc_id"),
            "text_excerpt": " ".join(str(raw.get("text_excerpt") or "").split())[:1200],
            "quality_score": score,
            "usable_for_core_claim": usable,
            "status": "valid" if usable else "context_only" if active and evidence_id else "quarantined",
            "metadata": {
                key: value
                for key, value in dict(raw.get("metadata") or {}).items()
                if key in {"claim_category", "event_type", "ticker", "title"}
            },
        }
        if not evidence_id:
            issues.append({"code": "evidence_id_missing", "severity": "blocker", "fields": []})
        items.append(item)
    usable_ids = [item["evidence_id"] for item in items if item["usable_for_core_claim"]]
    return {
        "status": "valid" if usable_ids else "missing",
        "items": items,
        "usable_evidence_ids": usable_ids,
        "issues": issues,
    }


def normalize_research_data(
    *,
    market: str,
    fundamentals: dict[str, Any] | None,
    valuation: dict[str, Any] | None,
    evidence: dict[str, Any] | None,
    risk: dict[str, Any] | None,
    freshness: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_fundamentals = normalize_fundamentals(fundamentals, market)
    normalized_valuation = normalize_valuation(valuation)
    normalized_evidence = normalize_evidence(evidence)
    return {
        "normalized_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fundamentals": normalized_fundamentals,
        "valuation": normalized_valuation,
        "evidence": normalized_evidence,
        "risk": {
            "alerts": list((risk or {}).get("alerts") or []),
            "freshness": dict(freshness or {}),
        },
    }
