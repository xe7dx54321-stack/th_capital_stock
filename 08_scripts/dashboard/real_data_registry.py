"""Real Data Registry for the SMR Dashboard.

Unified management of real data sources available to the Dashboard.
Provides source classification, priority ranking, and per-page
integration plans.

Important: This is a read-only registry. It does not write state,
does not access networks, does not read secrets, and does not
create data artifacts.
"""

from __future__ import annotations

from typing import Any


REAL_DATA_SOURCES: dict[str, dict[str, Any]] = {
    "source_registry": {
        "priority": "P0",
        "truth_status": "evidence_backed_real",
        "available": True,
        "provenance_confidence": "high",
        "fields": [
            "sources",
            "source_count",
            "health_status",
            "source_types",
            "last_sync",
        ],
        "pages": ["coverage", "signals", "health"],
        "has_source_url": True,
        "has_report_path": False,
        "has_evidence_packet": True,
        "description": "信息源注册表，包含所有已接入数据源的元数据",
    },
    "daily_report": {
        "priority": "P0",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "high",
        "fields": [
            "highlights",
            "published_at",
            "report_path",
            "themes",
            "summary",
        ],
        "pages": ["today", "signals", "research"],
        "has_source_url": False,
        "has_report_path": True,
        "has_evidence_packet": False,
        "description": "每日报告快照，包含当日重要信息和主题",
    },
    "evidence_gaps": {
        "priority": "P0",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "high",
        "fields": [
            "gaps",
            "gap_count",
            "entity",
            "missing_sources",
            "priority",
        ],
        "pages": ["today", "coverage", "signals", "research", "health"],
        "has_source_url": False,
        "has_report_path": False,
        "has_evidence_packet": True,
        "description": "证据缺口列表，标识覆盖对象的证据缺失情况",
    },
    "strategy_watch": {
        "priority": "P0",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "medium",
        "fields": [
            "top_focus_items",
            "watchlist",
            "thesis_data",
            "priority_items",
        ],
        "pages": ["today", "coverage", "research"],
        "has_source_url": False,
        "has_report_path": True,
        "has_evidence_packet": False,
        "description": "策略观察列表，包含重点关注对象和研究主题",
    },
    "overview": {
        "priority": "P0",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "medium",
        "fields": [
            "lag_days",
            "market_lag_days",
            "coverage_count",
            "signal_count",
            "health_score",
        ],
        "pages": ["today", "health"],
        "has_source_url": False,
        "has_report_path": False,
        "has_evidence_packet": False,
        "description": "Dashboard 总览统计，包含覆盖数、信号数、健康度等",
    },
    "run_log": {
        "priority": "P1",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "high",
        "fields": [
            "operations",
            "last_run",
            "run_status",
            "errors",
            "pipeline_summary",
        ],
        "pages": ["health"],
        "has_source_url": False,
        "has_report_path": True,
        "has_evidence_packet": False,
        "description": "运行日志和操作记录，包含流水线执行状态",
    },
    "opportunity_engine": {
        "priority": "P1",
        "truth_status": "real_snapshot_no_evidence",
        "available": True,
        "provenance_confidence": "medium",
        "fields": [
            "opportunities",
            "candidates",
            "radar",
        ],
        "pages": ["coverage", "research"],
        "has_source_url": False,
        "has_report_path": False,
        "has_evidence_packet": False,
        "description": "机会引擎输出，包含候选投资机会",
    },
    "market_events": {
        "priority": "P1",
        "truth_status": "real_snapshot_with_source",
        "available": True,
        "provenance_confidence": "medium",
        "fields": [
            "events",
            "event_count",
            "event_types",
        ],
        "pages": ["signals"],
        "has_source_url": True,
        "has_report_path": False,
        "has_evidence_packet": False,
        "description": "市场事件列表，包含价格异动和公告事件",
    },
    "risk_monitor": {
        "priority": "P2",
        "truth_status": "real_snapshot_no_evidence",
        "available": True,
        "provenance_confidence": "low",
        "fields": [
            "alerts",
            "issues",
            "risk_level",
        ],
        "pages": ["today", "health", "signals"],
        "has_source_url": False,
        "has_report_path": False,
        "has_evidence_packet": False,
        "description": "风险监控输出，包含风险提示和问题列表",
        "note": "风险监控数据需有 source_url 或 evidence_packet 才能进入主信号流",
    },
    "risk_decision": {
        "priority": "P2",
        "truth_status": "generated_summary",
        "available": True,
        "provenance_confidence": "none",
        "fields": [
            "decision",
            "sell_candidates",
            "trim_candidates",
        ],
        "pages": [],
        "has_source_url": False,
        "has_report_path": False,
        "has_evidence_packet": False,
        "description": "风险决策输出，多为生成式摘要",
        "note": "默认不进入主信号流，需有证据支撑才能展示",
    },
    "foundation_input_stream": {
        "priority": "P1",
        "truth_status": "pending_backend_integration",
        "available": False,
        "provenance_confidence": "none",
        "fields": [
            "evidence_packets",
            "source_health",
            "research_suggestions",
        ],
        "pages": ["coverage", "signals", "research", "health"],
        "has_source_url": True,
        "has_report_path": True,
        "has_evidence_packet": True,
        "description": "Foundation 证据输入流（待接入）",
        "note": "SMR-D7 阶段接入",
    },
}


def list_available_real_sources() -> list[str]:
    """List all available real data sources."""
    return [
        name
        for name, info in REAL_DATA_SOURCES.items()
        if info.get("available")
    ]


def classify_source_priority(source_name: str) -> str:
    """Classify a source by priority (P0/P1/P2/pending)."""
    info = REAL_DATA_SOURCES.get(source_name, {})
    return info.get("priority", "unknown")


def get_page_source_plan(page_name: str) -> list[dict[str, Any]]:
    """Get the real data integration plan for a specific page.

    Args:
        page_name: One of 'today', 'coverage', 'signals', 'research', 'health'.

    Returns:
        List of source info dicts relevant to the page, ordered by priority.
    """
    relevant = []
    for name, info in REAL_DATA_SOURCES.items():
        if page_name in info.get("pages", []):
            source_info = dict(info)
            source_info["source_name"] = name
            relevant.append(source_info)

    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    relevant.sort(key=lambda s: priority_order.get(s.get("priority", "P2"), 3))
    return relevant


def validate_source_has_provenance(item: dict[str, Any]) -> dict[str, Any]:
    """Validate that a data item has sufficient provenance information.

    Returns a dict with provenance assessment:
    - provenance_confidence: high/medium/low/none
    - has_source: bool
    - has_evidence: bool
    - has_timestamp: bool
    - missing_fields: list of missing provenance fields
    """
    evidence_keys = [
        "source_url", "original_url", "report_path",
        "evidence_packet_id", "evidence_id", "filing_url",
        "pdf_path", "source_rel_path", "source_refs", "evidence_url",
    ]
    source_keys = [
        "source_name", "source_type", "source_label",
        "provider", "org_name", "source_kind",
    ]
    timestamp_keys = [
        "published_at", "observed_at", "generated_at",
        "created_at", "alert_time", "event_time",
        "trade_date", "publish_time",
    ]

    has_evidence = any(item.get(k) for k in evidence_keys)
    has_source = any(item.get(k) for k in source_keys)
    has_timestamp = any(item.get(k) for k in timestamp_keys)

    missing = []
    if not has_source:
        missing.append("source_info")
    if not has_evidence:
        missing.append("evidence_indicator")
    if not has_timestamp:
        missing.append("timestamp")

    if has_evidence and has_timestamp and has_source:
        confidence = "high"
    elif has_source and (has_evidence or has_timestamp):
        confidence = "medium"
    elif has_source or has_timestamp:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "provenance_confidence": confidence,
        "has_source": has_source,
        "has_evidence_packet": has_evidence,
        "has_timestamp": has_timestamp,
        "missing_provenance_fields": missing,
    }


def summarize_real_data_coverage() -> dict[str, Any]:
    """Generate a summary of real data coverage across all sources."""
    available = []
    partial = []
    missing = []
    pending = []

    for name, info in REAL_DATA_SOURCES.items():
        if not info.get("available"):
            if info.get("truth_status") == "pending_backend_integration":
                pending.append(name)
            else:
                missing.append(name)
        elif info.get("provenance_confidence") in ("high", "medium"):
            available.append(name)
        else:
            partial.append(name)

    p0_count = sum(
        1 for info in REAL_DATA_SOURCES.values()
        if info.get("priority") == "P0" and info.get("available")
    )
    p1_count = sum(
        1 for info in REAL_DATA_SOURCES.values()
        if info.get("priority") == "P1" and info.get("available")
    )
    p2_count = sum(
        1 for info in REAL_DATA_SOURCES.values()
        if info.get("priority") == "P2" and info.get("available")
    )

    return {
        "total_sources": len(REAL_DATA_SOURCES),
        "available_sources": available,
        "partial_sources": partial,
        "missing_sources": missing,
        "pending_integrations": pending,
        "available_count": len(available),
        "partial_count": len(partial),
        "missing_count": len(missing),
        "pending_count": len(pending),
        "p0_available": p0_count,
        "p1_available": p1_count,
        "p2_available": p2_count,
    }
