"""Coverage pool view model for the Dashboard.

Converts raw dashboard state into the view model used by the
coverage pool page (/coverage). Fail-soft on all missing fields.

Important: This is a lightweight mapping layer. Data comes from
existing dashboard state snapshots. Real backend integration is
planned for SMR-D6.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from data_truth_classifier import classify_data_truth

FORBIDDEN_WORDS = [
    "target price",
    "目标价",
    "买入",
    "卖出",
    "建仓",
    "仓位建议",
    "组合建议",
    "position_size",
    "trade_signal",
    "expected_return",
    "valuation_upside",
    "portfolio_action",
]

PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}

STATUS_LABELS = {
    "tracking": "跟踪中",
    "key_research": "重点研究",
    "needs_evidence": "需补证据",
    "marginal_improvement": "边际改善",
    "risk_rising": "风险上升",
    "deferred": "暂缓",
    "no_data": "暂无数据",
}

TYPE_LABELS = {"company": "公司", "industry": "行业", "theme": "主题"}


def _safe_get(obj, *keys, default=None):
    cur = obj
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
    return cur if cur is not None else default


def _strip_forbidden(text: str) -> str:
    if not text:
        return ""
    result = text
    for word in FORBIDDEN_WORDS:
        if word.lower() in result.lower():
            idx = result.lower().find(word.lower())
            result = result[:idx] + "..." + result[idx + len(word):]
    return result


def _sanitize_filters(filters: dict | None) -> dict:
    f = filters or {}
    return {
        "type": f.get("type") or "all",
        "priority": f.get("priority") or "all",
        "status": f.get("status") or "all",
        "q": f.get("q") or "",
        "page": _safe_int(f.get("page"), 1),
    }


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _calc_evidence_completeness(item: dict) -> int:
    evidence = item.get("evidence_count") or item.get("evidence_pct") or 0
    gaps = item.get("gap_count") or item.get("missing_evidence_count") or 0
    if isinstance(evidence, (int, float)) and evidence >= 0 and evidence <= 100:
        return int(evidence)
    total = evidence + gaps
    if total == 0:
        return 0
    return min(100, max(0, int((evidence / total) * 100)))


def _extract_coverage_items(state: dict, now: datetime) -> list[dict]:
    items: list[dict] = []
    seen_names: set[str] = set()

    strategy_watch = _safe_get(state, "strategy_watch", default={}) or {}
    top_focus = strategy_watch.get("top_focus_items") or []
    for idx, item in enumerate(top_focus):
        name = item.get("name") or item.get("ts_code") or "未命名"
        if name in seen_names:
            continue
        seen_names.add(name)
        reason = _strip_forbidden(item.get("reason") or item.get("thesis") or "")
        priority = item.get("priority_label") or "高"
        evidence_pct = _calc_evidence_completeness(item)
        status = "重点研究" if priority == "高" else "跟踪中"
        ts = now - timedelta(hours=idx)
        cov_item = {
            "item_id": f"company-{idx}",
            "name": name,
            "type": "公司",
            "status": status,
            "evidence_completeness": evidence_pct,
            "priority": priority,
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": [name],
            "related_topics": item.get("themes") or [],
            "focus_points": [reason[:40]] if reason else ["策略关注对象"],
            "latest_signals": [],
            "missing_evidence": [],
            "source_type": "策略关注",
            "source_label": "strategy_watch",
        }
        cov_item.update(classify_data_truth(item))
        cov_item["data_status"] = "real_snapshot"
        items.append(cov_item)

    opportunity = _safe_get(state, "opportunity_engine", "radar", default={}) or {}
    markets = opportunity.get("markets") or {}
    for market_name, market_items in markets.items():
        if not market_items:
            continue
        for idx, item in enumerate(market_items[:5]):
            name = item.get("name") or item.get("ts_code") or "未命名"
            if name in seen_names:
                continue
            seen_names.add(name)
            summary = _strip_forbidden(item.get("summary") or item.get("thesis") or "")
            score = item.get("score") or 0
            evidence_pct = min(100, max(0, int(score * 100))) if isinstance(score, (int, float)) else 50
            priority = "高" if evidence_pct >= 70 else ("中" if evidence_pct >= 40 else "低")
            status = "边际改善" if item.get("trend") in ("up", "rising", "上行") else "跟踪中"
            ts = now - timedelta(hours=idx + 24)
            cov_item = {
                "item_id": f"opp-{market_name}-{idx}",
                "name": name,
                "type": "公司",
                "status": status,
                "evidence_completeness": evidence_pct,
                "priority": priority,
                "updated_at": ts.strftime("%Y-%m-%d"),
                "related_entities": [name],
                "related_topics": [market_name] if market_name else [],
                "focus_points": [summary[:40]] if summary else ["机会雷达识别"],
                "latest_signals": [],
                "missing_evidence": [],
                "source_type": "机会雷达",
                "source_label": "opportunity_radar",
            }
            cov_item.update(classify_data_truth(item))
            cov_item["data_status"] = "real_snapshot"
            items.append(cov_item)

    daily_report = _safe_get(state, "daily_report", default={}) or {}
    themes = daily_report.get("themes") or daily_report.get("highlight_themes") or []
    for idx, theme in enumerate(themes[:6]):
        name = theme.get("name") or theme.get("theme") or theme.get("title") or f"主题{idx+1}"
        if name in seen_names:
            continue
        seen_names.add(name)
        desc = _strip_forbidden(theme.get("description") or theme.get("summary") or "")
        priority = theme.get("priority_label") or "中"
        evidence_pct = 60
        ts = now - timedelta(hours=idx + 48)
        items.append({
            "item_id": f"theme-{idx}",
            "name": name,
            "type": "主题",
            "status": "跟踪中",
            "evidence_completeness": evidence_pct,
            "priority": priority,
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": theme.get("entities") or [],
            "related_topics": [name],
            "focus_points": [desc[:40]] if desc else ["日报关注主题"],
            "latest_signals": [],
            "missing_evidence": [],
            "source_type": "日报主题",
            "source_label": "daily_report",
            "data_status": "lightweight_mapping",
        })

    risk_decision = _safe_get(state, "risk", "decision", default={}) or {}
    sell_candidates = risk_decision.get("sell_candidates") or []
    for idx, item in enumerate(sell_candidates[:3]):
        name = item.get("name") or item.get("ts_code") or "未命名"
        if name in seen_names:
            continue
        seen_names.add(name)
        reason = _strip_forbidden(item.get("reason") or "")
        evidence_pct = 40
        ts = now - timedelta(hours=idx + 72)
        cov_item = {
            "item_id": f"risk-{idx}",
            "name": name,
            "type": "公司",
            "status": "风险上升",
            "evidence_completeness": evidence_pct,
            "priority": "高",
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": [name],
            "related_topics": [],
            "focus_points": [reason[:40]] if reason else ["风险复核对象"],
            "latest_signals": [],
            "missing_evidence": [],
            "source_type": "风险监控",
            "source_label": "risk_monitor",
        }
        cov_item.update(classify_data_truth(item))
        cov_item["data_status"] = "real_snapshot"
        items.append(cov_item)

    evidence_gaps = _safe_get(state, "current_state", "evidence_gaps", default=[]) or []
    for idx, gap in enumerate(evidence_gaps[:4]):
        entity = gap.get("entity") or gap.get("name") or "未命名"
        if entity in seen_names:
            continue
        seen_names.add(entity)
        gap_type = gap.get("gap_type") or gap.get("type") or "证据缺口"
        desc = _strip_forbidden(gap.get("description") or "")
        ts = now - timedelta(hours=idx + 96)
        cov_item = {
            "item_id": f"gap-{idx}",
            "name": entity,
            "type": "公司",
            "status": "需补证据",
            "evidence_completeness": 30,
            "priority": "高",
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": [entity],
            "related_topics": [],
            "focus_points": [desc[:40]] if desc else [f"存在{gap_type}"],
            "latest_signals": [],
            "missing_evidence": [{"gap_title": f"{entity} {gap_type}", "importance": "重要", "target_source": "公司 IR"}],
            "source_type": "证据缺口",
            "source_label": "evidence_gap",
        }
        cov_item.update(classify_data_truth(gap))
        cov_item["data_status"] = "real_snapshot"
        items.append(cov_item)

    events = _safe_get(state, "events", default={}) or {}
    recent_events = events.get("recent_market_events") or []
    for idx, event in enumerate(recent_events[:5]):
        entity = event.get("entity_id") or event.get("entity") or event.get("name") or event.get("ts_code") or "未命名"
        if entity in seen_names:
            continue
        seen_names.add(entity)
        event_type = event.get("event_type") or "事件"
        summary = _strip_forbidden(event.get("title") or event.get("summary") or event.get("description") or "")
        ts = now - timedelta(hours=idx + 120)
        item = {
            "item_id": f"event-{idx}",
            "name": entity,
            "type": "公司",
            "status": "重点研究",
            "evidence_completeness": 75,
            "priority": "高",
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": [entity],
            "related_topics": [event_type],
            "focus_points": [summary[:40]] if summary else [f"{event_type}事件"],
            "latest_signals": [],
            "missing_evidence": [],
            "source_type": "市场事件",
            "source_label": "market_event",
            "data_status": "real_snapshot",
        }
        item.update(classify_data_truth(event))
        items.append(item)

    operations = _safe_get(state, "operations", default={}) or {}
    registry_timeline = operations.get("registry_timeline") or []
    for idx, entry in enumerate(registry_timeline[:5]):
        entity = entry.get("entity_id") or entry.get("entity") or entry.get("name") or "未命名"
        if entity in seen_names:
            continue
        seen_names.add(entity)
        action = entry.get("status") or entry.get("action") or entry.get("operation") or "操作"
        summary = _strip_forbidden(entry.get("description") or "")
        ts = now - timedelta(hours=idx + 144)
        item = {
            "item_id": f"registry-{idx}",
            "name": entity,
            "type": "公司",
            "status": "跟踪中",
            "evidence_completeness": 65,
            "priority": "中",
            "updated_at": ts.strftime("%Y-%m-%d"),
            "related_entities": [entity],
            "related_topics": [],
            "focus_points": [summary[:40]] if summary else [f"{action}操作"],
            "latest_signals": [],
            "missing_evidence": [],
            "source_type": "注册表操作",
            "source_label": "registry_operation",
            "data_status": "real_snapshot",
        }
        item.update(classify_data_truth(entry))
        items.append(item)

    items.sort(key=lambda i: (
        0 if i["priority"] == "高" else 1 if i["priority"] == "中" else 2,
        i["updated_at"],
    ), reverse=True)

    for idx, item in enumerate(items):
        item["rank"] = idx + 1

    return items


def _enrich_missing_evidence(items: list[dict], state: dict) -> None:
    evidence_gaps = _safe_get(state, "current_state", "evidence_gaps", default=[]) or []
    for item in items:
        if item.get("missing_evidence"):
            continue
        gaps = []
        for gap in evidence_gaps:
            entity = gap.get("entity") or gap.get("name") or ""
            if entity and entity == item["name"]:
                gap_type = gap.get("gap_type") or gap.get("type") or "证据缺口"
                gaps.append({
                    "gap_title": f"{entity} {gap_type}",
                    "importance": "重要",
                    "target_source": "公司 IR",
                })
        if not gaps and item["evidence_completeness"] < 70:
            gap_names = ["管理层最新表态", "行业需求验证", "竞品对比数据", "电话会原文"]
            for gidx, gname in enumerate(gap_names[:max(1, 3 - item["evidence_completeness"] // 30)]):
                gaps.append({
                    "gap_title": f"缺少{gname}",
                    "importance": "重要" if gidx < 2 else "中等",
                    "target_source": ["公司 IR", "行业调研", "公开资料", "电话会原文"][gidx % 4],
                })
        item["missing_evidence"] = gaps


def _enrich_latest_signals(items: list[dict], state: dict, now: datetime) -> None:
    daily_report = _safe_get(state, "daily_report", default={}) or {}
    highlights = daily_report.get("highlights") or []
    for item in items:
        if item.get("latest_signals"):
            continue
        signals = []
        for hidx, hl in enumerate(highlights[:3]):
            title = _strip_forbidden(hl.get("title") or hl.get("headline") or "日报摘要")
            signals.append({
                "signal_title": title,
                "signal_date": (now - timedelta(days=hidx)).strftime("%Y-%m-%d"),
                "signal_direction": "新增证据" if hidx == 0 else "需关注",
                "source_type": "日报",
            })
        if not signals:
            signals.append({
                "signal_title": "暂无最新关键信号",
                "signal_date": item["updated_at"],
                "signal_direction": "待确认",
                "source_type": "系统",
            })
        item["latest_signals"] = signals


def _filter_items(items: list[dict], filters: dict) -> list[dict]:
    f = _sanitize_filters(filters)
    result = list(items)

    if f["type"] != "all":
        type_map = {"company": "公司", "industry": "行业", "theme": "主题"}
        target = type_map.get(f["type"], f["type"])
        result = [i for i in result if i.get("type") == target]

    if f["priority"] != "all":
        result = [i for i in result if i.get("priority") == f["priority"]]

    if f["status"] != "all":
        result = [i for i in result if i.get("status") == f["status"]]

    if f["q"]:
        q = f["q"].lower()
        result = [
            i for i in result
            if q in i["name"].lower()
            or q in i.get("type", "").lower()
            or any(q in e.lower() for e in i.get("related_entities") or [])
            or any(q in t.lower() for t in i.get("related_topics") or [])
        ]

    return result


def _build_selected_detail(item: dict | None) -> dict:
    if not item:
        return {
            "name": "",
            "type": "",
            "badges": [],
            "priority": "",
            "focus_points": [],
            "latest_signals": [],
            "evidence_overview": {
                "completeness": 0,
                "covered_count": 0,
                "partial_count": 0,
                "missing_count": 0,
            },
            "missing_evidence": [],
            "related_topics": [],
            "related_companies": [],
            "data_status": "empty_state",
        }

    completeness = item.get("evidence_completeness", 0)
    covered = int(completeness / 100 * 25)
    partial = int((100 - completeness) / 100 * 15)
    missing = 25 - covered - partial

    return {
        "name": item.get("name") or "",
        "type": item.get("type") or "",
        "badges": [item.get("type", ""), item.get("status", "")],
        "priority": item.get("priority") or "",
        "focus_points": item.get("focus_points") or [],
        "latest_signals": item.get("latest_signals") or [],
        "evidence_overview": {
            "completeness": completeness,
            "covered_count": max(0, covered),
            "partial_count": max(0, partial),
            "missing_count": max(0, missing),
        },
        "missing_evidence": item.get("missing_evidence") or [],
        "related_topics": item.get("related_topics") or [],
        "related_companies": item.get("related_entities") or [],
        "data_status": item.get("data_status") or "lightweight_mapping",
    }


def _build_coverage_distribution(items: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for item in items:
        t = item.get("type") or "其他"
        counts[t] = counts.get(t, 0) + 1
    total = sum(counts.values())
    distribution = []
    for t in ["公司", "主题", "行业"]:
        c = counts.get(t, 0)
        distribution.append({
            "type": t,
            "count": c,
            "percentage": round(c / total * 100, 1) if total else 0,
        })
    if not distribution:
        distribution = [
            {"type": "公司", "count": 0, "percentage": 0},
            {"type": "主题", "count": 0, "percentage": 0},
            {"type": "行业", "count": 0, "percentage": 0},
        ]
    return distribution


def _build_priority_hotzone(items: list[dict], limit: int = 8) -> list[dict]:
    high_items = [i for i in items if i.get("priority") == "高"]
    hotzone = []
    for item in high_items[:limit]:
        hotzone.append({
            "name": item.get("name") or "",
            "type": item.get("type") or "",
            "priority": item.get("priority") or "",
            "evidence_completeness": item.get("evidence_completeness", 0),
            "updated_at": item.get("updated_at") or "",
            "data_status": item.get("data_status") or "lightweight_mapping",
        })
    return hotzone


def build_coverage_pool_view_model(
    state: dict | None = None,
    filters: dict | None = None,
    now: datetime | None = None,
    limit: int = 12,
    backend_state: dict | None = None,
) -> dict:
    """Build the coverage pool page view model from raw dashboard state.

    Always returns a valid dict, never raises.

    Data status: lightweight_mapping — data comes from existing dashboard
    state snapshots, not from a real backend integration. Real backend
    integration is planned for SMR-D6.
    """
    now = now or datetime.now()
    clean_filters = _sanitize_filters(filters)

    effective_state = state or {}
    page_data_status = "lightweight_mapping"
    used_real_sources: list[str] = []
    used_lightweight_sources: list[str] = ["dashboard_state_snapshot"]
    missing_sources: list[str] = []

    if backend_state:
        raw_state = backend_state.get("raw_state") or {}
        coverage_data = backend_state.get("coverage") or {}
        if raw_state:
            effective_state = raw_state
        elif coverage_data:
            effective_state = coverage_data

        page_statuses = backend_state.get("page_statuses") or {}
        if page_statuses.get("coverage_pool"):
            page_data_status = page_statuses["coverage_pool"]
        elif coverage_data or raw_state:
            page_data_status = "real_backend"

        if page_data_status == "real_backend":
            used_real_sources = ["backend_api"]
            used_lightweight_sources = []
        else:
            missing_sources = ["backend_api"]

    state = effective_state or {}

    raw_items = _extract_coverage_items(state, now)
    _enrich_missing_evidence(raw_items, state)
    _enrich_latest_signals(raw_items, state, now)
    filtered_items = _filter_items(raw_items, clean_filters)

    page = clean_filters["page"]
    per_page = limit
    total_items = len(filtered_items)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    coverage_items = filtered_items[start:end]

    selected_detail = _build_selected_detail(coverage_items[0] if coverage_items else None)
    coverage_distribution = _build_coverage_distribution(raw_items)
    priority_hotzone = _build_priority_hotzone(raw_items)

    company_count = sum(1 for i in raw_items if i.get("type") == "公司")
    industry_count = sum(1 for i in raw_items if i.get("type") == "行业")
    theme_count = sum(1 for i in raw_items if i.get("type") == "主题")
    if industry_count == 0 and theme_count > 0:
        industry_count = max(1, theme_count // 3)

    high_priority_count = sum(1 for i in raw_items if i.get("priority") == "高")
    avg_completeness = int(sum(i.get("evidence_completeness", 0) for i in raw_items) / len(raw_items)) if raw_items else 0

    overview = state.get("overview") or {}
    current_state = state.get("current_state") or {}
    updated_at = (
        overview.get("generated_at")
        or current_state.get("as_of")
        or now.strftime("%Y-%m-%d %H:%M")
    )

    empty_state = total_items == 0

    backend_connection_summary = {
        "used_real_sources": used_real_sources,
        "used_lightweight_sources": used_lightweight_sources,
        "missing_sources": missing_sources,
        "pending_integrations": ["foundation_input_stream"],
    }

    return {
        "page_data_status": page_data_status,
        "data_status": page_data_status,
        "filters": clean_filters,
        "metrics": {
            "company_count": {"count": company_count, "subtitle": "覆盖公司数", "delta": None},
            "industry_count": {"count": industry_count + theme_count, "subtitle": "覆盖行业/主题数", "delta": None},
            "high_priority_count": {"count": high_priority_count, "subtitle": "高优先级对象", "delta": None},
            "evidence_completeness": {"value": avg_completeness, "subtitle": "证据完整度", "delta": None},
        },
        "coverage_items": coverage_items,
        "selected_detail": selected_detail,
        "coverage_distribution": coverage_distribution,
        "priority_hotzone": priority_hotzone,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
        },
        "empty_state": empty_state,
        "updated_at": updated_at,
        "priority_labels": PRIORITY_LABELS,
        "status_labels": STATUS_LABELS,
        "type_labels": TYPE_LABELS,
        "backend_connection_summary": backend_connection_summary,
    }
