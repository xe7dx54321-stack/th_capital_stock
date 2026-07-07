"""Backend Data Provider for the SMR Dashboard.

Unified read-only access layer for backend data sources.
Wraps existing dashboard state loader with fail-soft behavior
and data status tracking.

Important: This is a read-only provider. It does not write any
state, does not create data artifacts, does not access networks,
and does not expose secrets.

Data status levels:
- real_snapshot: data comes from real DB snapshot with complete fields
- partial_snapshot: data comes from real DB but fields are incomplete
- lightweight_mapping: derived from existing state, not a true business loop
- empty_state: no usable data available
- pending_backend_integration: module exists but not yet integrated
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from real_data_registry import summarize_real_data_coverage
from evidence_provenance_resolver import summarize_provenance

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


def _safe_build_state(db_path: str | None = None) -> dict[str, Any] | None:
    try:
        from smr_dashboard import build_dashboard_state

        return build_dashboard_state()
    except Exception:
        return None


def _extract_overview_data(state: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if not state:
        return {}, "empty_state"

    has_overview = bool(state.get("overview"))
    has_daily = bool(state.get("daily") or state.get("daily_report"))
    has_risk = bool(state.get("risk"))
    has_strategy = bool(state.get("strategy_watch"))

    sources = [has_overview, has_daily, has_risk, has_strategy]
    available = sum(1 for s in sources if s)

    if available == 0:
        return {}, "empty_state"
    if available >= 3:
        return state, "real_snapshot"
    return state, "partial_snapshot"


def _extract_coverage_data(state: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if not state:
        return {}, "empty_state"

    has_pools = bool(state.get("pools"))
    has_strategy = bool(state.get("strategy_watch"))
    has_opportunity = bool(state.get("opportunity_engine"))
    has_positions = bool(state.get("positions"))

    sources = [has_pools, has_strategy, has_opportunity, has_positions]
    available = sum(1 for s in sources if s)

    if available == 0:
        return {}, "empty_state"
    if available >= 3:
        return state, "real_snapshot"
    return state, "partial_snapshot"


def _extract_signals_data(state: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if not state:
        return {}, "empty_state"

    has_risk = bool(state.get("risk"))
    has_daily = bool(state.get("daily") or state.get("daily_report"))
    has_events = bool(state.get("market_events"))
    has_registry = bool(state.get("source_registry") or state.get("input_source_registry"))

    sources = [has_risk, has_daily, has_events, has_registry]
    available = sum(1 for s in sources if s)

    if available == 0:
        return {}, "empty_state"
    if available >= 3:
        return state, "real_snapshot"
    return state, "partial_snapshot"


def _extract_research_data(state: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if not state:
        return {}, "empty_state"

    has_evidence_gaps = bool(state.get("evidence_gaps"))
    has_strategy = bool(state.get("strategy_watch"))
    has_opportunity = bool(state.get("opportunity_engine"))
    has_research = bool(state.get("research") or state.get("investment_research"))

    sources = [has_evidence_gaps, has_strategy, has_opportunity, has_research]
    available = sum(1 for s in sources if s)

    if available == 0:
        return {}, "empty_state"
    if available >= 2:
        return state, "partial_snapshot"
    return state, "lightweight_mapping"


def _extract_health_data(state: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if not state:
        return {}, "empty_state"

    has_freshness = bool(state.get("data_freshness"))
    has_registry = bool(state.get("source_registry") or state.get("input_source_registry"))
    has_risk = bool(state.get("risk"))
    has_run_log = bool(state.get("run_log"))

    sources = [has_freshness, has_registry, has_risk, has_run_log]
    available = sum(1 for s in sources if s)

    if available == 0:
        return {}, "empty_state"
    if available >= 3:
        return state, "real_snapshot"
    return state, "partial_snapshot"


def load_dashboard_backend_state(
    db_path: str | None = None,
    artifact_root: str | None = None,
    allow_missing: bool = True,
) -> dict[str, Any]:
    """Load unified backend state for all 5 dashboard pages.

    This is a read-only operation. It never writes state, never
    creates artifacts, never accesses networks, and never exposes
    secrets. Missing DB or files result in empty/partial state
    rather than exceptions.

    Args:
        db_path: Optional path to SQLite DB. Uses default if None.
        artifact_root: Optional path to artifact root. Uses default if None.
        allow_missing: If True, missing sources return empty state
            instead of raising.

    Returns:
        Dict with backend_status, page-specific data sections,
        missing_sources list, and warnings list.
    """
    now = datetime.now()
    warnings: list[str] = []
    missing_sources: list[str] = []
    sources_checked = 0
    sources_available = 0

    raw_state = None
    try:
        raw_state = _safe_build_state(db_path)
        sources_checked += 1
        if raw_state:
            sources_available += 1
        else:
            missing_sources.append("dashboard_db_snapshot")
            warnings.append("Dashboard DB snapshot unavailable or empty")
    except Exception as e:
        if not allow_missing:
            raise
        missing_sources.append("dashboard_db_snapshot")
        warnings.append(f"Failed to load dashboard state: {type(e).__name__}")
        raw_state = None

    overview_data, overview_status = _extract_overview_data(raw_state)
    coverage_data, coverage_status = _extract_coverage_data(raw_state)
    signals_data, signals_status = _extract_signals_data(raw_state)
    research_data, research_status = _extract_research_data(raw_state)
    health_data, health_status = _extract_health_data(raw_state)

    page_statuses = [
        overview_status,
        coverage_status,
        signals_status,
        research_status,
        health_status,
    ]

    if all(s == "real_snapshot" for s in page_statuses):
        overall_status = "real_snapshot"
    elif any(s == "empty_state" for s in page_statuses) and all(
        s in ("empty_state", "lightweight_mapping") for s in page_statuses
    ):
        overall_status = "lightweight_mapping"
    elif any(s in ("real_snapshot", "partial_snapshot") for s in page_statuses):
        overall_status = "partial_snapshot"
    else:
        overall_status = "empty_state"

    updated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    if raw_state and raw_state.get("generated_at"):
        updated_at = str(raw_state["generated_at"])

    used_real_sources: list[str] = []
    used_lightweight_sources: list[str] = []
    pending_integrations: list[str] = ["foundation_input_stream"]

    real_data_coverage = summarize_real_data_coverage()

    all_signal_items: list[dict[str, Any]] = []
    if raw_state:
        if isinstance(raw_state.get("daily_report"), dict):
            highlights = raw_state["daily_report"].get("highlights", [])
            if isinstance(highlights, list):
                all_signal_items.extend(highlights)
        if isinstance(raw_state.get("evidence_gaps"), dict):
            gaps = raw_state["evidence_gaps"].get("gaps", [])
            if isinstance(gaps, list):
                all_signal_items.extend(gaps)
        if isinstance(raw_state.get("source_registry"), dict):
            sources = raw_state["source_registry"].get("sources", [])
            if isinstance(sources, list):
                all_signal_items.extend(sources)
        if isinstance(raw_state.get("market_events"), dict):
            events = raw_state["market_events"].get("events", [])
            if isinstance(events, list):
                all_signal_items.extend(events)

    provenance_summary = summarize_provenance(all_signal_items) if all_signal_items else {
        "total_count": 0,
        "high_confidence_count": 0,
        "medium_confidence_count": 0,
        "low_confidence_count": 0,
        "none_confidence_count": 0,
        "evidence_backed_count": 0,
        "source_backed_count": 0,
        "generated_summary_count": 0,
        "default_fallback_count": 0,
        "placeholder_count": 0,
        "main_flow_eligible_count": 0,
        "filtered_out_count": 0,
    }

    if overview_status in ("real_snapshot", "partial_snapshot"):
        used_real_sources.append("overview/daily/risk/strategy")
    else:
        used_lightweight_sources.append("overview_fallback")

    if coverage_status in ("real_snapshot", "partial_snapshot"):
        used_real_sources.append("pools/strategy/opportunity")
    else:
        used_lightweight_sources.append("coverage_fallback")

    if signals_status in ("real_snapshot", "partial_snapshot"):
        used_real_sources.append("risk/events/daily")
    else:
        used_lightweight_sources.append("signals_fallback")

    if research_status in ("real_snapshot", "partial_snapshot"):
        used_real_sources.append("evidence_gaps/strategy")
    else:
        used_lightweight_sources.append("research_fallback")

    if health_status in ("real_snapshot", "partial_snapshot"):
        used_real_sources.append("freshness/registry/run_log")
    else:
        used_lightweight_sources.append("health_fallback")

    return {
        "backend_status": {
            "overall_status": overall_status,
            "updated_at": updated_at,
            "sources_checked": sources_checked,
            "sources_available": sources_available,
            "sources_missing": len(missing_sources),
            "data_status": overall_status,
        },
        "overview": overview_data,
        "coverage": coverage_data,
        "signals": signals_data,
        "research_queue": research_data,
        "health": health_data,
        "raw_state": raw_state or {},
        "raw_refs": {
            "db_path": db_path,
            "artifact_root": artifact_root,
        },
        "page_statuses": {
            "today_overview": overview_status,
            "coverage_pool": coverage_status,
            "signal_flow": signals_status,
            "research_queue": research_status,
            "data_health": health_status,
        },
        "backend_connection_summary": {
            "used_real_sources": used_real_sources,
            "used_lightweight_sources": used_lightweight_sources,
            "missing_sources": missing_sources,
            "pending_integrations": pending_integrations,
        },
        "real_data_inventory": real_data_coverage,
        "evidence_provenance_summary": provenance_summary,
        "missing_sources": missing_sources,
        "warnings": warnings,
    }
