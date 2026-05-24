"""Financial unit normalization helpers for A/H fundamentals.

The extraction layer often receives a field value and a nearby unit string
separately.  These helpers keep unit parsing explicit so ambiguous values do
not accidentally become promotion-grade evidence.
"""

from __future__ import annotations

import re
from typing import Any


AMOUNT_FIELDS = {
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
}
EPS_FIELDS = {"eps_basic", "eps_diluted"}
RATIO_FIELDS = {"gross_margin", "operating_margin", "net_margin", "roe", "roic"}

DEFAULT_CURRENCY_BY_MARKET = {"A": "CNY", "H": "HKD", "HK": "HKD", "US": "USD"}

_CURRENCY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"人民币|人民幣|\bRMB\b|\bCNY\b", re.I), "CNY"),
    (re.compile(r"港币|港幣|港元|\bHKD\b|HK\$", re.I), "HKD"),
    (re.compile(r"美元|美金|\bUSD\b|US\$", re.I), "USD"),
]

_SCALE_PATTERNS: list[tuple[re.Pattern[str], float, str]] = [
    (re.compile(r"亿元|億元|hundred\s*million", re.I), 100_000_000.0, "hundred_million"),
    (re.compile(r"百万元|百萬(?:元)?|\bmillion\b", re.I), 1_000_000.0, "million"),
    (re.compile(r"万元|萬元|ten\s*thousand", re.I), 10_000.0, "ten_thousand"),
    (re.compile(r"千元|千(?:元)?|\bthousand\b", re.I), 1_000.0, "thousand"),
    (re.compile(r"\bbillion\b", re.I), 1_000_000_000.0, "billion"),
]


def default_currency_for_market(market: str | None) -> str:
    return DEFAULT_CURRENCY_BY_MARKET.get(str(market or "").upper(), "CNY")


def normalize_numeric(value: Any) -> float | None:
    if value in (None, "", "-", "--", "None", "nan"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    try:
        parsed = float(text)
    except ValueError:
        return None
    return -abs(parsed) if negative else parsed


def _combined_unit_text(raw_unit: Any, table_header: Any = None, context: Any = None) -> tuple[str, bool]:
    explicit = str(raw_unit or "").strip()
    if explicit:
        return explicit, False
    inferred = " ".join(str(item or "").strip() for item in (table_header, context) if str(item or "").strip())
    return inferred, True


def _detect_currency(text: str, market: str | None) -> tuple[str, bool, bool]:
    matches = [currency for pattern, currency in _CURRENCY_PATTERNS if pattern.search(text or "")]
    unique = list(dict.fromkeys(matches))
    if len(unique) > 1:
        return default_currency_for_market(market), False, True
    if unique:
        return unique[0], False, False
    return default_currency_for_market(market), True, False


def _detect_scale(text: str) -> tuple[float, str, bool]:
    for pattern, scale, label in _SCALE_PATTERNS:
        if pattern.search(text or ""):
            return scale, label, False
    return 1.0, "unit", True


def _has_percentage_marker(text: str) -> bool:
    lower = str(text or "").lower()
    return "%" in lower or "百分比" in lower or "percent" in lower or "margin" in lower or "rate" in lower


def normalize_financial_unit(
    raw_value: Any,
    raw_unit: Any = None,
    *,
    field: str | None = None,
    market: str | None = None,
    table_header: Any = None,
    context: Any = None,
) -> dict[str, Any]:
    """Normalize a raw financial value/unit pair.

    ``normalized_value`` is useful for newly parsed values.  Existing pipeline
    values may already be scaled, so callers can use the confidence and warning
    fields without replacing their stored numeric value.
    """

    field = str(field or "")
    raw_numeric = normalize_numeric(raw_value)
    unit_text, unit_inferred = _combined_unit_text(raw_unit, table_header=table_header, context=context)
    context_text = " ".join(str(item or "") for item in (unit_text, context, table_header))
    detection_text = unit_text if raw_unit not in (None, "") else context_text
    if field in RATIO_FIELDS:
        return {
            "raw_value": raw_value,
            "raw_unit": raw_unit,
            "normalized_value": raw_numeric,
            "normalized_unit": "ratio",
            "scale": 1.0,
            "currency": None,
            "unit_confidence": 0.95 if raw_numeric is not None else 0.0,
            "unit_inferred": False,
            "unit_warning": None,
            "allowed_usage": "supporting_evidence" if raw_numeric is not None else "blocked",
        }
    currency, currency_inferred, currency_conflict = _detect_currency(detection_text, market)
    if field in EPS_FIELDS:
        warning = "ambiguous_unit" if currency_conflict or (not unit_text and currency_inferred) else None
        confidence = 0.9 if not warning and not currency_inferred else (0.68 if not currency_conflict else 0.25)
        return {
            "raw_value": raw_value,
            "raw_unit": raw_unit,
            "normalized_value": raw_numeric,
            "normalized_unit": f"{currency}/share",
            "scale": 1.0,
            "currency": currency,
            "unit_confidence": confidence,
            "unit_inferred": bool(currency_inferred or unit_inferred),
            "unit_warning": warning,
            "allowed_usage": "blocked" if warning == "ambiguous_unit" else "supporting_evidence",
        }

    percentage_context = _has_percentage_marker(unit_text) or (raw_unit in (None, "") and _has_percentage_marker(context_text))
    if percentage_context and field in AMOUNT_FIELDS:
        return {
            "raw_value": raw_value,
            "raw_unit": raw_unit,
            "normalized_value": None,
            "normalized_unit": currency,
            "scale": 1.0,
            "currency": currency,
            "unit_confidence": 0.2,
            "unit_inferred": bool(unit_inferred or currency_inferred),
            "unit_warning": "percentage_not_amount",
            "allowed_usage": "blocked",
        }

    scale, scale_label, scale_inferred = _detect_scale(detection_text)
    if currency_conflict:
        confidence = 0.2
        warning = "ambiguous_unit"
    elif not unit_text and scale_inferred:
        confidence = 0.2
        warning = "ambiguous_unit"
    elif unit_inferred or currency_inferred or scale_inferred:
        confidence = 0.68 if scale_label != "unit" or not currency_inferred else 0.62
        warning = "unit inferred from table header" if unit_inferred and scale_label != "unit" else None
    else:
        confidence = 0.95
        warning = None

    normalized_value = None if raw_numeric is None else raw_numeric * scale
    return {
        "raw_value": raw_value,
        "raw_unit": raw_unit,
        "normalized_value": normalized_value,
        "normalized_unit": currency,
        "scale": scale,
        "currency": currency,
        "unit_confidence": round(confidence, 3),
        "unit_inferred": bool(unit_inferred or currency_inferred or scale_inferred),
        "unit_warning": warning,
        "allowed_usage": "blocked" if warning in {"ambiguous_unit", "percentage_not_amount"} else "supporting_evidence",
        "unit_label": scale_label,
    }
