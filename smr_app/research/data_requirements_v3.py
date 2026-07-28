from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from smr_app.acquisition.contracts import AuthorityTier, DataRequirement
from smr_app.acquisition.store import AcquisitionStore


FINANCIAL_FIELDS = (
    "revenue",
    "net_profit_parent",
    "net_profit_excluding_nonrecurring",
    "operating_cash_flow",
    "eps",
    "weighted_roe",
    "total_assets",
    "attributable_equity",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _configured_identity(ticker: str) -> dict[str, Any]:
    path = PROJECT_ROOT / "config" / "cninfo_identities.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        identity = (payload.get("identities") or {}).get(ticker, {})
        return dict(identity) if isinstance(identity, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _configured_security_name(ticker: str) -> str:
    return str(_configured_identity(ticker).get("security_name") or "")


REQUIREMENT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "data_type": "official_filings",
        "required_fields": ("announcement_index", "raw_document", "full_text"),
        "maximum_age_seconds": 24 * 60 * 60,
        "minimum_authority": AuthorityTier.OFFICIAL,
        "section_ids": ("company_business", "products_moat", "operations", "financials", "risks"),
        "critical": True,
    },
    {
        "data_type": "financial_statements",
        "required_fields": FINANCIAL_FIELDS,
        "maximum_age_seconds": 30 * 24 * 60 * 60,
        "minimum_authority": AuthorityTier.OFFICIAL,
        "section_ids": ("financials", "growth", "valuation", "scenarios"),
        "critical": True,
    },
    {
        "data_type": "daily_bars",
        "required_fields": ("trade_date", "open", "high", "low", "close", "volume"),
        "maximum_age_seconds": 36 * 60 * 60,
        "minimum_authority": AuthorityTier.REPUTABLE_SECONDARY,
        "section_ids": ("peers", "valuation", "tracking"),
        "critical": False,
    },
    {
        "data_type": "realtime_quote",
        "required_fields": ("price", "quote_time", "currency"),
        "maximum_age_seconds": 5 * 60,
        "minimum_authority": AuthorityTier.REPUTABLE_SECONDARY,
        "section_ids": ("valuation",),
        "critical": False,
    },
    {
        "data_type": "valuation_snapshot",
        "required_fields": ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of"),
        "maximum_age_seconds": 60 * 60,
        "minimum_authority": AuthorityTier.REPUTABLE_SECONDARY,
        "section_ids": ("valuation", "scenarios"),
        "critical": False,
    },
    {
        "data_type": "peer_comparison",
        "required_fields": ("peer_set", "selection_reason", "comparable_metrics", "as_of"),
        "maximum_age_seconds": 7 * 24 * 60 * 60,
        "minimum_authority": AuthorityTier.REPUTABLE_SECONDARY,
        "section_ids": ("industry", "peers", "valuation"),
        "critical": False,
    },
    {
        "data_type": "news_research",
        "required_fields": ("raw_document", "source_url", "evidence_candidates"),
        "maximum_age_seconds": 12 * 60 * 60,
        "minimum_authority": AuthorityTier.REPUTABLE_SECONDARY,
        "section_ids": ("industry", "catalysts", "risks", "tracking"),
        "critical": False,
    },
)


def build_stock_data_requirement_manifest(
    ticker: str,
    market: str,
    plan: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    now = generated_at or datetime.now(timezone.utc)
    identity = _configured_identity(ticker)
    security_name = str(identity.get("security_name") or "")
    official_research_urls = [
        str(url)
        for url in (identity.get("official_research_urls") or [])
        if isinstance(url, str) and url.startswith(("http://", "https://"))
    ]
    planned_sections = {str(item.get("section_id")) for item in plan.get("sections") or []}
    requirements = []
    for spec in REQUIREMENT_SPECS:
        section_ids = tuple(section_id for section_id in spec["section_ids"] if section_id in planned_sections)
        requirements.append({
            "requirement_id": f"{ticker}:{spec['data_type']}",
            "entity_key": ticker,
            "market": market,
            "data_type": spec["data_type"],
            "as_of": None,
            "required_fields": list(spec["required_fields"]),
            "maximum_age_seconds": int(spec["maximum_age_seconds"]),
            "minimum_authority": spec["minimum_authority"].value,
            "section_ids": list(section_ids),
            "critical": bool(spec["critical"]),
            "acquisition_metadata": {
                "search_query": (
                    f"{security_name} {ticker.split('.')[0]} {ticker} 最新消息"
                ).strip(),
                "search_queries": [
                    f"{security_name} {ticker.split('.')[0]} 业绩 营收 净利润",
                    f"{security_name} 光模块 AI 业务 行业",
                    f"{security_name} 订单 产能 催化",
                    f"{security_name} 风险 竞争 格局",
                ],
                "search_limit": 4,
                "preferred_domains": ["cnstock.com", "stcn.com", "cls.cn", "jiemian.com"],
                "relevance_terms": [term for term in (security_name, ticker.split(".")[0]) if term],
                "urls": official_research_urls,
            } if spec["data_type"] == "news_research" else {},
        })
    return {
        "manifest_version": "1.0",
        "entity_key": ticker,
        "market": market,
        "generated_at": now.astimezone(timezone.utc).isoformat(),
        "requirements": requirements,
    }


def requirement_from_manifest_item(item: Mapping[str, Any]) -> DataRequirement:
    maximum_age_seconds = item.get("maximum_age_seconds")
    return DataRequirement(
        entity_key=str(item["entity_key"]),
        data_type=str(item["data_type"]),
        market=str(item["market"]),
        as_of=str(item["as_of"]) if item.get("as_of") else None,
        required_fields=tuple(str(field) for field in item.get("required_fields") or []),
        maximum_age=timedelta(seconds=int(maximum_age_seconds)) if maximum_age_seconds is not None else None,
        minimum_authority=AuthorityTier(str(item.get("minimum_authority") or AuthorityTier.DISCOVERY.value)),
        metadata={
            "requirement_id": item.get("requirement_id"),
            "section_ids": list(item.get("section_ids") or []),
            "critical": bool(item.get("critical")),
            **dict(item.get("acquisition_metadata") or {}),
        },
    )


def _latest(values: list[Any]) -> str | None:
    normalized = [str(value) for value in values if value]
    return max(normalized) if normalized else None


def _legacy_probe(data_type: str, research_context: Mapping[str, Any], structured: Mapping[str, Any]) -> dict[str, Any]:
    corpus = research_context.get("corpus") or {}
    instruments = research_context.get("instruments") or {}
    target = instruments.get("target") or {}
    if data_type == "official_filings":
        filings = corpus.get("filings") or []
        chunks = corpus.get("chunks") or []
        usable = bool(filings and chunks and any(len(str(item.get("text") or "")) >= 200 for item in chunks))
        return {
            "usable": usable,
            "available_through": _latest([item.get("published_at") for item in filings]),
            "reason": "formal_documents_and_full_text_present" if usable else "formal_document_or_full_text_missing",
        }
    if data_type == "financial_statements":
        snapshot = structured.get("fundamentals") or target.get("fundamentals") or {}
        present = {field for field in FINANCIAL_FIELDS if snapshot.get(field) is not None}
        return {
            "usable": bool(snapshot),
            "available_through": snapshot.get("period") or snapshot.get("created_at"),
            "reason": "legacy_fundamentals_present" if snapshot else "fundamentals_missing",
            "present_fields": sorted(present),
        }
    if data_type == "daily_bars":
        bars = target.get("daily_bars") or []
        return {
            "usable": bool(bars),
            "available_through": _latest([item.get("trade_date") for item in bars]),
            "reason": "daily_bars_present" if bars else "daily_bars_missing",
        }
    if data_type == "realtime_quote":
        quote = target.get("quote") or {}
        return {
            "usable": bool(quote and quote.get("price") is not None),
            "available_through": quote.get("quote_time"),
            "reason": "realtime_quote_present" if quote else "realtime_quote_missing",
        }
    if data_type == "valuation_snapshot":
        valuation = structured.get("valuation") or target.get("valuation") or {}
        return {
            "usable": bool(valuation),
            "available_through": valuation.get("generated_at"),
            "reason": "valuation_present" if valuation else "valuation_missing",
        }
    if data_type == "peer_comparison":
        peers = research_context.get("graph", {}).get("peers") or []
        peer_instruments = instruments.get("peers") or []
        usable = bool(peers and peer_instruments)
        return {
            "usable": usable,
            "available_through": _latest([
                bar.get("trade_date")
                for instrument in peer_instruments
                for bar in (instrument.get("daily_bars") or [])[:1]
            ]),
            "reason": "peer_set_and_instruments_present" if usable else "peer_set_or_instruments_missing",
        }
    if data_type == "news_research":
        items = [*(corpus.get("news") or []), *(corpus.get("events") or [])]
        return {
            "usable": bool(items),
            "available_through": _latest([item.get("published_at") or item.get("event_date") for item in items]),
            "reason": "news_or_events_present" if items else "news_and_events_missing",
        }
    return {"usable": False, "available_through": None, "reason": "unsupported_data_type"}


def evaluate_cached_requirements(
    manifest: Mapping[str, Any],
    store: AcquisitionStore,
    research_context: Mapping[str, Any],
    structured: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    checked_at = now or datetime.now(timezone.utc)
    items = []
    for manifest_item in manifest.get("requirements") or []:
        requirement = requirement_from_manifest_item(manifest_item)
        state = store.get_dataset_state(requirement)
        if state and state.satisfies(requirement, checked_at):
            items.append({
                **dict(manifest_item),
                "cache_status": "fresh",
                "cache_source": "acquisition_store",
                "usable": True,
                "refresh_needed": False,
                "available_through": state.available_through,
                "reason": "write_through_dataset_is_fresh",
                "dataset_state": asdict(state),
            })
            continue
        legacy = _legacy_probe(requirement.data_type, research_context, structured)
        items.append({
            **dict(manifest_item),
            "cache_status": "stale_or_unregistered" if legacy["usable"] else "missing",
            "cache_source": "legacy_source_db" if legacy["usable"] else None,
            "usable": bool(legacy["usable"]),
            "refresh_needed": True,
            "available_through": legacy.get("available_through"),
            "reason": "write_through_state_missing_or_stale:" + str(legacy["reason"]),
            "present_fields": legacy.get("present_fields") or [],
            "dataset_state": asdict(state) if state else None,
        })
    return {
        "checked_at": checked_at.astimezone(timezone.utc).isoformat(),
        "items": items,
        "fresh_requirements": sum(1 for item in items if not item["refresh_needed"]),
        "usable_requirements": sum(1 for item in items if item["usable"]),
        "refresh_required": sum(1 for item in items if item["refresh_needed"]),
    }


def validate_acquisition_results(
    cache_evaluation: Mapping[str, Any],
    results: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    items = []
    for cached in cache_evaluation.get("items") or []:
        requirement_id = str(cached["requirement_id"])
        result = dict(results.get(requirement_id) or {})
        acquired = result.get("status") in {"cache_hit", "acquired"}
        conflict = result.get("status") == "acquired_with_conflicts"
        usable = bool(cached.get("usable")) or acquired
        refresh_resolved = not cached.get("refresh_needed") or acquired
        items.append({
            "requirement_id": requirement_id,
            "data_type": cached["data_type"],
            "critical": bool(cached.get("critical")),
            "usable": usable and not conflict,
            "refresh_resolved": refresh_resolved and not conflict,
            "status": result.get("status") or ("cache_satisfied" if not cached.get("refresh_needed") else "not_attempted"),
            "provider_id": result.get("provider_id"),
            "errors": result.get("errors") or [],
        })
    unresolved = [item for item in items if not item["refresh_resolved"]]
    critical_unusable = [item for item in items if item["critical"] and not item["usable"]]
    return {
        "status": "blocked" if critical_unusable else "degraded" if unresolved else "passed",
        "total_requirements": len(items),
        "usable_requirements": sum(1 for item in items if item["usable"]),
        "resolved_requirements": sum(1 for item in items if item["refresh_resolved"]),
        "unresolved_requirements": len(unresolved),
        "critical_unusable": [item["data_type"] for item in critical_unusable],
        "items": items,
    }
