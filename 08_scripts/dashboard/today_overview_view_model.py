"""View model adapter for the Today Overview dashboard page.

This module transforms the raw dashboard state dict into a clean,
presentation-ready structure for the Today Overview page. It does
not introduce any new investment logic -- it only reshapes existing
data for display.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _fmt_count(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _pick_top_changes(state: dict, limit: int = 3) -> list[dict]:
    changes: list[dict] = []

    risk_decision = _safe_get(state, "risk", "decision") or {}
    for candidate in (risk_decision.get("sell_candidates") or [])[:2]:
        name = candidate.get("name") or candidate.get("ts_code") or "未命名标的"
        reason = candidate.get("reason") or candidate.get("summary") or ""
        severity = candidate.get("severity") or candidate.get("risk_level") or "medium"
        changes.append(
            {
                "rank": 0,
                "title": f"{name} 出现风险信号",
                "affected_entities": [name],
                "summary": reason[:80] if reason else "系统检测到风险信号，建议关注。",
                "evidence_strength": "高" if severity in ("high", "critical", "高") else "中",
                "source_type": "风险监控",
                "source_label": "risk_monitor",
                "status_or_action": "待关注",
                "category": "risk",
            }
        )

    opportunity_engine = _safe_get(state, "opportunity_engine") or {}
    radar = opportunity_engine.get("radar") or {}
    top_candidates = radar.get("top_candidates") or []
    for item in top_candidates[:2]:
        name = item.get("name") or item.get("ts_code") or "未命名标的"
        thesis = item.get("thesis") or item.get("summary") or ""
        score = item.get("score") or item.get("priority") or 0
        if any(c["affected_entities"] and c["affected_entities"][0] == name for c in changes):
            continue
        strength = "高" if (isinstance(score, (int, float)) and score >= 0.7) else "中"
        changes.append(
            {
                "rank": 0,
                "title": f"{name} 出现边际变化",
                "affected_entities": [name],
                "summary": thesis[:80] if thesis else "系统检测到值得关注的边际变化。",
                "evidence_strength": strength,
                "source_type": "机会雷达",
                "source_label": "opportunity_radar",
                "status_or_action": "观察中",
                "category": "opportunity",
            }
        )

    current_state = _safe_get(state, "current_state") or {}
    evidence_gaps = current_state.get("evidence_gaps") or []
    for gap in evidence_gaps[:1]:
        entity = gap.get("entity") or gap.get("name") or "研究对象"
        gap_desc = gap.get("description") or gap.get("gap_type") or ""
        changes.append(
            {
                "rank": 0,
                "title": f"{entity} 存在证据缺口",
                "affected_entities": [entity],
                "summary": gap_desc[:80] if gap_desc else "关键证据尚不完整，建议补充研究。",
                "evidence_strength": "待补",
                "source_type": "证据缺口",
                "source_label": "evidence_gap",
                "status_or_action": "待补证据",
                "category": "evidence_gap",
            }
        )

    sorted_changes = sorted(
        changes,
        key=lambda c: (
            0 if c["category"] == "risk" else 1 if c["category"] == "evidence_gap" else 2,
            c.get("evidence_strength") != "高",
        ),
    )

    for idx, item in enumerate(sorted_changes[:limit]):
        item["rank"] = idx + 1

    return sorted_changes[:limit]


def _pick_pending_decisions(state: dict, limit: int = 3) -> list[dict]:
    decisions: list[dict] = []

    current_state = _safe_get(state, "current_state") or {}
    evidence_gaps = current_state.get("evidence_gaps") or []
    for gap in evidence_gaps:
        entity = gap.get("entity") or gap.get("name") or "研究对象"
        gap_type = gap.get("gap_type") or gap.get("category") or "证据缺口"
        decisions.append(
            {
                "rank": 0,
                "question": f"{entity} {gap_type}是否需要补充研究？",
                "status_badge": "待补证据",
                "badge_tone": "warning",
            }
        )

    portfolio = _safe_get(state, "portfolio_action") or {}
    actions = portfolio.get("actions") or []
    for action in actions[:2]:
        subject = (action.get("subject") or {}).get("name") or action.get("action_id") or "动作"
        action_mode = action.get("action_mode") or action.get("type") or ""
        decisions.append(
            {
                "rank": 0,
                "question": f"{subject} 动作建议是否确认？",
                "status_badge": "待确认",
                "badge_tone": "info",
            }
        )
        if len(decisions) >= limit:
            break

    if not decisions:
        research_synth = _safe_get(state, "reporting", "research_synthesis") or {}
        if research_synth.get("pending_review_count"):
            decisions.append(
                {
                    "rank": 1,
                    "question": "是否复核最新研究综合结论？",
                    "status_badge": "可进入研究",
                    "badge_tone": "success",
                }
            )

    for idx, item in enumerate(decisions[:limit]):
        item["rank"] = idx + 1

    return decisions[:limit]


def _build_coverage_moves(state: dict, limit: int = 5) -> list[dict]:
    moves: list[dict] = []

    opportunity_engine = _safe_get(state, "opportunity_engine") or {}
    radar = opportunity_engine.get("radar") or {}
    for market_items in (radar.get("markets") or {}).values():
        for item in (market_items or [])[:limit]:
            name = item.get("name") or item.get("ts_code") or "-"
            score = item.get("score") or 0
            trend = item.get("trend") or item.get("momentum") or ""
            if trend in ("up", "rising", "上行"):
                status_label = "强势上行"
                status_tone = "good"
            elif trend in ("down", "falling", "下行"):
                status_label = "风险上升"
                status_tone = "danger"
            else:
                status_label = "横盘震荡"
                status_tone = "muted"
            evidence_pct = min(100, max(0, int((score or 0) * 100))) if isinstance(score, (int, float)) else 0
            priority = item.get("priority_label") or ("高" if evidence_pct >= 70 else "中" if evidence_pct >= 40 else "低")
            moves.append(
                {
                    "company": name,
                    "status_label": status_label,
                    "status_tone": status_tone,
                    "evidence_pct": evidence_pct,
                    "priority": priority,
                }
            )
            if len(moves) >= limit:
                break
        if len(moves) >= limit:
            break

    if not moves:
        strategy = _safe_get(state, "strategy_watch") or {}
        for item in (strategy.get("top_focus_items") or [])[:limit]:
            name = item.get("name") or item.get("ts_code") or "-"
            moves.append(
                {
                    "company": name,
                    "status_label": "观察中",
                    "status_tone": "muted",
                    "evidence_pct": 0,
                    "priority": item.get("priority_label") or "中",
                }
            )

    return moves[:limit]


def _build_health_summary(state: dict) -> list[dict]:
    overview = _safe_get(state, "overview") or {}
    a_gap = overview.get("a_share_expected_gap_days") or 0
    hk_gap = overview.get("hk_expected_gap_days") or 0
    us_gap = overview.get("us_expected_gap_days") or 0
    overall_market_fresh = (a_gap == 0 or hk_gap == 0 or us_gap == 0)

    market_status = "正常" if overall_market_fresh else "需关注"
    market_tone = "good" if overall_market_fresh else "warning"

    source_registry = _safe_get(state, "source_registry") or {}
    source_status_counts = source_registry.get("counts_by_status") or {}
    total_sources = source_registry.get("source_count") or 0
    healthy_sources = source_status_counts.get("healthy") or source_status_counts.get("ok") or 0
    source_status = "正常" if (total_sources and healthy_sources == total_sources) else "需关注"
    source_tone = "good" if source_status == "正常" else "warning"
    if not total_sources:
        source_status = "暂无数据"
        source_tone = "muted"

    operations = _safe_get(state, "operations") or {}
    scheduler = operations.get("scheduler") or {}
    today_status = scheduler.get("today_status_counts") or {}
    failed = today_status.get("failed") or 0
    pipeline_status = "正常" if failed == 0 else "异常"
    pipeline_tone = "good" if failed == 0 else "danger"

    return [
        {
            "label": "行情新鲜度",
            "status": market_status,
            "tone": market_tone,
        },
        {
            "label": "信息源状态",
            "status": source_status,
            "tone": source_tone,
        },
        {
            "label": "Pipeline 状态",
            "status": pipeline_status,
            "tone": pipeline_tone,
        },
    ]


def _compute_metrics(state: dict, top_changes: list, pending: list, coverage_moves: list, health_items: list) -> dict:
    risk_count = 0
    risk_decision = _safe_get(state, "risk", "decision") or {}
    sell_candidates = risk_decision.get("sell_candidates") or []
    risk_count = sum(
        1 for c in sell_candidates
        if str(c.get("verdict") or "").lower() in {"sell", "trim", "高", "high", "critical"}
    )
    if risk_count == 0:
        risk_payload = _safe_get(state, "risk") or {}
        risk_count = risk_payload.get("snapshot_alert_count") or risk_payload.get("snapshot_unacknowledged_alert_count") or 0

    high_priority_count = 0
    strategy = _safe_get(state, "strategy_watch") or {}
    priority_counts = strategy.get("priority_counts") or {}
    high_priority_count = priority_counts.get("high") or priority_counts.get("高") or 0
    if high_priority_count == 0:
        high_priority_count = len(coverage_moves)

    changes_count = len(top_changes)
    if changes_count == 0:
        market_events = _safe_get(state, "events", "recent_market_events") or []
        changes_count = min(5, len(market_events))

    pending_count = len(pending)
    if pending_count == 0:
        current_state = _safe_get(state, "current_state") or {}
        pending_count = current_state.get("pending_review_count") or 0

    return {
        "important_changes": {
            "count": changes_count,
            "subtitle": f"今日检测到 {changes_count} 条重要变化",
        },
        "pending_decisions": {
            "count": pending_count,
            "subtitle": f"{pending_count} 项关键事项待确认",
        },
        "high_priority_companies": {
            "count": high_priority_count,
            "subtitle": "覆盖池中优先跟进标的",
        },
        "risk_alerts": {
            "count": risk_count,
            "subtitle": f"{risk_count} 项需重点关注的风险",
        },
    }


def build_today_overview_view_model(
    state: dict | None = None,
    now: datetime | None = None,
    backend_state: dict | None = None,
) -> dict:
    """Adapt raw dashboard state into a Today Overview view model.

    The function is fail-soft: missing state or missing sub-dicts will
    produce an empty-state view model rather than raising.
    """
    now = now or datetime.now()

    effective_state = state or {}
    page_data_status = "lightweight_mapping"
    used_real_sources: list[str] = []
    used_lightweight_sources: list[str] = ["dashboard_state_snapshot"]
    missing_sources: list[str] = []

    if backend_state:
        raw_state = backend_state.get("raw_state") or {}
        overview_data = backend_state.get("overview") or {}
        if raw_state:
            effective_state = raw_state
        elif overview_data:
            effective_state = overview_data

        page_statuses = backend_state.get("page_statuses") or {}
        if page_statuses.get("today_overview"):
            page_data_status = page_statuses["today_overview"]
        elif overview_data or raw_state:
            page_data_status = "real_backend"

        if page_data_status == "real_backend":
            used_real_sources = ["backend_api"]
            used_lightweight_sources = []
        else:
            missing_sources = ["backend_api"]

    state = effective_state or {}

    top_changes = _pick_top_changes(state, limit=3)
    pending_decisions = _pick_pending_decisions(state, limit=3)
    coverage_moves = _build_coverage_moves(state, limit=5)
    health_summary = _build_health_summary(state)
    metrics = _compute_metrics(state, top_changes, pending_decisions, coverage_moves, health_summary)

    has_data = bool(
        top_changes
        or pending_decisions
        or coverage_moves
        or any(h["status"] not in ("暂无数据",) for h in health_summary)
    )

    updated_at = ""
    candidate_sources = [
        _safe_get(state, "overview", "generated_at"),
        _safe_get(state, "reporting", "daily_reporting", "created_at"),
        _safe_get(state, "strategy_watch", "created_at"),
    ]
    for s in candidate_sources:
        if s:
            updated_at = str(s)
            break
    if not updated_at:
        updated_at = now.strftime("%Y-%m-%d %H:%M")

    backend_connection_summary = {
        "used_real_sources": used_real_sources,
        "used_lightweight_sources": used_lightweight_sources,
        "missing_sources": missing_sources,
        "pending_integrations": ["foundation_input_stream"],
    }

    return {
        "page_data_status": page_data_status,
        "data_status": page_data_status,
        "metrics": metrics,
        "top_changes": top_changes,
        "pending_decisions": pending_decisions,
        "coverage_moves": coverage_moves,
        "health_summary": health_summary,
        "updated_at": updated_at,
        "empty_state": not has_data,
        "backend_connection_summary": backend_connection_summary,
    }
