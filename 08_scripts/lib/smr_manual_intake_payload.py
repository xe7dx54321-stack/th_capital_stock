#!/usr/bin/env python3
"""Phase 43 manual intake payload fixtures."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


CORE_SAMPLE_NAMES = [
    "official_consensus_authorized_sample",
    "supplier_share_scenario_sample",
    "customer_allocation_proxy_sample",
]

INVALID_SAMPLE_NAMES = [
    "bad_consensus_internal_proxy",
]

SAMPLE_ALIASES = {
    "official_consensus": "official_consensus_authorized_sample",
    "official_consensus_authorized": "official_consensus_authorized_sample",
    "official_consensus_authorized_sample": "official_consensus_authorized_sample",
    "supplier_share": "supplier_share_scenario_sample",
    "supplier_share_scenario": "supplier_share_scenario_sample",
    "supplier_share_scenario_sample": "supplier_share_scenario_sample",
    "confirmed_customer_allocation": "customer_allocation_proxy_sample",
    "customer_allocation": "customer_allocation_proxy_sample",
    "customer_allocation_proxy": "customer_allocation_proxy_sample",
    "customer_allocation_proxy_sample": "customer_allocation_proxy_sample",
    "bad_consensus_proxy": "bad_consensus_internal_proxy",
    "official_consensus_internal_proxy": "bad_consensus_internal_proxy",
    "bad_consensus_internal_proxy": "bad_consensus_internal_proxy",
}


def _ticker_slug(ticker: str) -> str:
    return normalize_ticker(ticker).split(".")[0].lower()


def _base_payload(ticker: str) -> dict[str, Any]:
    return {
        "ticker": normalize_ticker(ticker),
        "raw_file_attached": False,
    }


def _official_consensus_payload(ticker: str) -> dict[str, Any]:
    slug = _ticker_slug(ticker)
    return {
        **_base_payload(ticker),
        "intake_id": f"manual_intake_{slug}_official_consensus_sample",
        "evidence_type": "official_consensus",
        "source_type": "authorized_consensus_source",
        "source_title": "Sample Authorized Consensus Source",
        "source_provider": "sample_provider",
        "source_date": "2026-05-24",
        "source_url_or_reference": "manual://sample_authorized_consensus",
        "permission_status": "authorized_or_user_provided",
        "quoted_span": "Sample quoted span describing consensus benchmark.",
        "requested_allowed_usage": "expectation_gap_benchmark",
        "user_notes": "sample only",
        "limitations": [
            "sample payload only",
            "authorized source metadata must be reviewed before use",
            "candidate is not confirmed evidence",
        ],
    }


def _supplier_share_payload(ticker: str) -> dict[str, Any]:
    slug = _ticker_slug(ticker)
    return {
        **_base_payload(ticker),
        "intake_id": f"manual_intake_{slug}_supplier_share_scenario",
        "evidence_type": "supplier_share",
        "source_type": "scenario_assumption",
        "source_title": "Sample Supplier Share Scenario Assumption",
        "source_provider": "manual_research_assumption",
        "source_date": "2026-05-24",
        "source_url_or_reference": "manual://sample_supplier_share_scenario",
        "permission_status": "user_provided_assumption",
        "quoted_span": "Sample assumption note for supplier share sensitivity only.",
        "requested_allowed_usage": "supporting_evidence",
        "user_notes": "sample only; value is explicitly an assumption",
        "limitations": [
            "scenario assumption only",
            "not publicly confirmed",
            "do not treat as supplier share fact",
        ],
    }


def _customer_allocation_payload(ticker: str) -> dict[str, Any]:
    slug = _ticker_slug(ticker)
    return {
        **_base_payload(ticker),
        "intake_id": f"manual_intake_{slug}_customer_allocation_proxy",
        "evidence_type": "confirmed_customer_allocation",
        "source_type": "proxy_evidence_note",
        "source_title": "Sample Customer Allocation Proxy Note",
        "source_provider": "manual_research_note",
        "source_date": "2026-05-24",
        "source_url_or_reference": "manual://sample_customer_allocation_proxy",
        "permission_status": "user_provided_note",
        "quoted_span": "Sample proxy note referencing customer demand but not confirmed allocation.",
        "requested_allowed_usage": "supporting_evidence",
        "user_notes": "sample only; proxy evidence cannot confirm allocation",
        "limitations": [
            "proxy only",
            "no direct customer-side allocation statement",
            "do not treat as confirmed customer allocation",
        ],
    }


def _bad_consensus_proxy_payload(ticker: str) -> dict[str, Any]:
    slug = _ticker_slug(ticker)
    return {
        **_base_payload(ticker),
        "intake_id": f"manual_intake_{slug}_bad_consensus_proxy",
        "evidence_type": "official_consensus",
        "source_type": "proxy_evidence_note",
        "source_title": "Bad Internal Consensus Proxy",
        "source_provider": "internal_model",
        "source_date": "2026-05-24",
        "source_url_or_reference": "",
        "permission_status": "internal_only",
        "quoted_span": "Internal proxy note attempting to stand in for consensus.",
        "requested_allowed_usage": "expectation_gap_benchmark",
        "user_notes": "invalid sample; must be rejected",
        "limitations": [
            "internal proxy only",
            "not authorized consensus",
            "must not be used as official consensus",
        ],
    }


SAMPLE_BUILDERS = {
    "official_consensus_authorized_sample": _official_consensus_payload,
    "supplier_share_scenario_sample": _supplier_share_payload,
    "customer_allocation_proxy_sample": _customer_allocation_payload,
    "bad_consensus_internal_proxy": _bad_consensus_proxy_payload,
}


def canonical_sample_name(sample: str) -> str:
    key = str(sample or "").strip()
    if key not in SAMPLE_ALIASES:
        raise ValueError(f"Unsupported Phase 43 manual intake sample: {sample}")
    return SAMPLE_ALIASES[key]


def build_manual_intake_payload(ticker: str = TARGET_REVIEW_TICKER, sample: str = "official_consensus") -> dict[str, Any]:
    canonical = canonical_sample_name(sample)
    return dict(SAMPLE_BUILDERS[canonical](ticker))


def list_manual_intake_payloads(
    ticker: str = TARGET_REVIEW_TICKER,
    *,
    include_invalid: bool = False,
    sample: str | None = None,
) -> list[dict[str, Any]]:
    if sample:
        return [build_manual_intake_payload(ticker, sample)]
    names = list(CORE_SAMPLE_NAMES)
    if include_invalid:
        names.extend(INVALID_SAMPLE_NAMES)
    return [build_manual_intake_payload(ticker, name) for name in names]


def build_manual_intake_samples_payload(ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    payloads = list_manual_intake_payloads(ticker)
    return {
        "generated_at": now_ts(),
        "ticker": normalize_ticker(ticker),
        "manual_intake_samples": {
            "samples": payloads,
            "sample_count": len(payloads),
            "sample_payloads_are_real_data": False,
            "raw_file_attached": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "sample_only": True,
            "evidence_written": False,
            "raw_file_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
