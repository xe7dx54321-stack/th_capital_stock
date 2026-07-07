"""Signal flow view model for the Dashboard.

Converts raw dashboard state into the view model used by the
signal flow page (/signals). Fail-soft on all missing fields.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from html import escape

from data_truth_classifier import classify_data_truth, should_enter_main_signal_flow

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

SOURCE_TYPE_LABELS = {
    "official_disclosure": "官方披露",
    "company_ir": "公司 IR",
    "public_research": "公开研究",
    "media_excerpt": "媒体摘录",
    "earnings_call": "电话会纪要",
    "foundation": "Foundation",
    "risk_monitor": "风险监控",
}

STRENGTH_TONES = {
    "高": "high",
    "中": "medium",
    "低": "low",
    "待确认": "unknown",
}

REVIEW_STATUS_LABELS = {
    "confirmed": "已确认",
    "needs_review": "待复核",
    "needs_evidence": "待补证据",
    "deferred": "暂缓",
}


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


def _format_time_label(ts: datetime | None, now: datetime) -> str:
    if not ts:
        return ""
    delta = now - ts
    if delta.days == 0:
        return ts.strftime("%H:%M")
    if delta.days == 1:
        return "昨天 " + ts.strftime("%H:%M")
    if delta.days < 7:
        return f"{delta.days}天前"
    return ts.strftime("%m-%d %H:%M")


def _sanitize_filters(filters: dict | None) -> dict:
    f = filters or {}
    return {
        "time_range": f.get("time_range") or "all",
        "source_type": f.get("source_type") or "all",
        "entity": f.get("entity") or "all",
        "strength": f.get("strength") or "all",
        "q": f.get("q") or "",
    }


def _extract_signals_from_state(state: dict, now: datetime, enable_quality_gate: bool = True) -> dict:
    all_signals: list[dict] = []
    filtered_signals: list[dict] = []
    low_confidence_candidates: list[dict] = []

    risk_decision = _safe_get(state, "risk", "decision", default={}) or {}
    sell_candidates = risk_decision.get("sell_candidates") or []
    for idx, item in enumerate(sell_candidates):
        name = item.get("name") or item.get("ts_code") or "未知标的"
        reason = _strip_forbidden(item.get("reason") or item.get("summary") or "")
        ts = now - timedelta(hours=idx + 1)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": f"{name} 风险提示",
            "summary": reason[:80] if reason else "系统检测到风险因素",
            "source_type": "risk_monitor",
            "source_label": "风险监控",
            "related_entities": [name],
            "related_topics": [],
            "evidence_strength": "高",
            "timestamp_confidence": "MEDIUM",
            "review_status": "待复核",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": ["risk"],
        }
        signal.update(classify_data_truth(item))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(item):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    evidence_gaps = _safe_get(state, "current_state", "evidence_gaps", default=[]) or []
    for idx, gap in enumerate(evidence_gaps):
        entity = gap.get("entity") or gap.get("name") or "未知对象"
        gap_type = gap.get("gap_type") or gap.get("type") or "证据缺口"
        desc = _strip_forbidden(gap.get("description") or "")
        ts = now - timedelta(hours=idx + 2)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": f"{entity} {gap_type}",
            "summary": desc[:80] if desc else "存在证据缺口，需要补充",
            "source_type": "foundation",
            "source_label": "证据缺口",
            "related_entities": [entity],
            "related_topics": [],
            "evidence_strength": "待确认",
            "timestamp_confidence": "LOW",
            "review_status": "待补证据",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": [],
        }
        signal.update(classify_data_truth(gap))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(gap):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    strategy_watch = _safe_get(state, "strategy_watch", default={}) or {}
    top_focus = strategy_watch.get("top_focus_items") or []
    for idx, item in enumerate(top_focus):
        name = item.get("name") or item.get("ts_code") or "关注标的"
        reason = _strip_forbidden(item.get("reason") or item.get("thesis") or "")
        ts = now - timedelta(hours=idx + 3)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": f"{name} 进入重点关注",
            "summary": reason[:80] if reason else "策略系统纳入重点关注",
            "source_type": "public_research",
            "source_label": "策略研究",
            "related_entities": [name],
            "related_topics": [],
            "evidence_strength": "中",
            "timestamp_confidence": "MEDIUM",
            "review_status": "已确认",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": [],
        }
        signal.update(classify_data_truth(item))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(item):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    opportunity = _safe_get(state, "opportunity", default={}) or {}
    markets = opportunity.get("markets") or {}
    for market_name, items in markets.items():
        if not items:
            continue
        for idx, item in enumerate(items[:3]):
            name = item.get("name") or item.get("ts_code") or "机会标的"
            summary = _strip_forbidden(item.get("summary") or item.get("reason") or "")
            ts = now - timedelta(hours=idx + 4)
            signal = {
                "timestamp": ts,
                "time_label": _format_time_label(ts, now),
                "title": f"{name} 机会雷达更新",
                "summary": summary[:80] if summary else "机会雷达有新变化",
                "source_type": "public_research",
                "source_label": "机会雷达",
                "related_entities": [name],
                "related_topics": [market_name] if market_name else [],
                "evidence_strength": "中",
                "timestamp_confidence": "MEDIUM",
                "review_status": "已确认",
                "source_url": None,
                "evidence_url": None,
                "risk_flags": [],
            }
            signal.update(classify_data_truth(item))
            all_signals.append(signal)
            if enable_quality_gate and should_enter_main_signal_flow(item):
                filtered_signals.append(signal)
            elif not enable_quality_gate:
                filtered_signals.append(signal)
            else:
                low_confidence_candidates.append(signal)

    risk_monitor = _safe_get(state, "risk", "monitor", default={}) or {}
    risk_items = risk_monitor.get("alerts") or risk_monitor.get("items") or []
    for idx, item in enumerate(risk_items):
        title = _strip_forbidden(item.get("title") or item.get("name") or "风险事件")
        desc = _strip_forbidden(item.get("description") or item.get("detail") or "")
        ts = now - timedelta(hours=idx + 5)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": title,
            "summary": desc[:80] if desc else "风险监控检测到异常",
            "source_type": "risk_monitor",
            "source_label": "风险监控",
            "related_entities": item.get("entities") or item.get("related") or [],
            "related_topics": [],
            "evidence_strength": "高",
            "timestamp_confidence": "HIGH",
            "review_status": "待复核",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": ["risk"],
        }
        signal.update(classify_data_truth(item))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(item):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    daily_report = _safe_get(state, "daily_report", default={}) or {}
    summary_items = daily_report.get("highlights") or daily_report.get("summary_items") or []
    for idx, item in enumerate(summary_items):
        title = _strip_forbidden(item.get("title") or item.get("headline") or "今日摘要")
        desc = _strip_forbidden(item.get("content") or item.get("summary") or "")
        ts = now - timedelta(hours=idx + 6)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": title,
            "summary": desc[:80] if desc else "",
            "source_type": "public_research",
            "source_label": "日报摘要",
            "related_entities": item.get("entities") or [],
            "related_topics": item.get("topics") or [],
            "evidence_strength": "中",
            "timestamp_confidence": "MEDIUM",
            "review_status": "已确认",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": [],
        }
        signal.update(classify_data_truth(item))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(item):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    events = _safe_get(state, "events", default={}) or {}
    recent_events = events.get("recent_market_events") or []
    for idx, event in enumerate(recent_events[:5]):
        entity = event.get("entity_id") or event.get("entity") or event.get("name") or event.get("ts_code") or "市场事件"
        event_type = event.get("event_type") or "事件"
        summary = _strip_forbidden(event.get("title") or event.get("summary") or event.get("description") or "")
        ts = now - timedelta(hours=idx + 7)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": f"{entity} {event_type}",
            "summary": summary[:80] if summary else f"发生{event_type}事件，值得关注",
            "source_type": "official_disclosure",
            "source_label": "市场事件",
            "related_entities": [entity],
            "related_topics": [],
            "evidence_strength": "高",
            "timestamp_confidence": "HIGH",
            "review_status": "已确认",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": [],
            "data_status": "real_snapshot",
        }
        signal.update(classify_data_truth(event))
        all_signals.append(signal)
        if enable_quality_gate and should_enter_main_signal_flow(event):
            filtered_signals.append(signal)
        elif not enable_quality_gate:
            filtered_signals.append(signal)
        else:
            low_confidence_candidates.append(signal)

    operations = _safe_get(state, "operations", default={}) or {}
    registry_timeline = operations.get("registry_timeline") or []
    for idx, entry in enumerate(registry_timeline[:5]):
        entity = entry.get("entity_id") or entry.get("entity") or entry.get("name") or "数据项"
        action = entry.get("status") or entry.get("action") or entry.get("operation") or "操作"
        summary = _strip_forbidden(entry.get("description") or "")
        ts = now - timedelta(hours=idx + 8)
        signal = {
            "timestamp": ts,
            "time_label": _format_time_label(ts, now),
            "title": f"{entity} {action}",
            "summary": summary[:80] if summary else f"{entity}状态更新为{action}",
            "source_type": "foundation",
            "source_label": "注册表操作",
            "related_entities": [entity],
            "related_topics": [],
            "evidence_strength": "中",
            "timestamp_confidence": "MEDIUM",
            "review_status": "已确认",
            "source_url": None,
            "evidence_url": None,
            "risk_flags": [],
            "data_status": "real_snapshot",
        }
        signal.update(classify_data_truth(entry))
        all_signals.append(signal)
        # registry_timeline is real backend operational data; allow it into
        # the main signal flow even without an external evidence URL.
        filtered_signals.append(signal)

    filtered_signals.sort(key=lambda s: s["timestamp"], reverse=True)
    return {
        "signals": filtered_signals,
        "filtered_signal_count": len(all_signals) - len(filtered_signals),
        "low_confidence_candidate_count": len(low_confidence_candidates),
    }


def _filter_signals(signals: list[dict], filters: dict, now: datetime) -> list[dict]:
    f = _sanitize_filters(filters)
    result = list(signals)

    if f["time_range"] == "24h":
        cutoff = now - timedelta(hours=24)
        result = [s for s in result if s["timestamp"] >= cutoff]
    elif f["time_range"] == "7d":
        cutoff = now - timedelta(days=7)
        result = [s for s in result if s["timestamp"] >= cutoff]
    elif f["time_range"] == "30d":
        cutoff = now - timedelta(days=30)
        result = [s for s in result if s["timestamp"] >= cutoff]

    if f["source_type"] != "all":
        result = [s for s in result if s["source_type"] == f["source_type"]]

    if f["entity"] == "company":
        result = [s for s in result if s["related_entities"]]
    elif f["entity"] == "industry":
        result = [s for s in result if any(t for t in s["related_topics"])]
    elif f["entity"] == "theme":
        result = [s for s in result if s["related_topics"]]

    if f["strength"] != "all":
        result = [s for s in result if s["evidence_strength"] == f["strength"]]

    if f["q"]:
        q = f["q"].lower()
        result = [
            s for s in result
            if q in s["title"].lower()
            or q in s["summary"].lower()
            or any(q in e.lower() for e in s["related_entities"])
            or any(q in t.lower() for t in s["related_topics"])
        ]

    return result


def _aggregate_hot_entities(signals: list[dict]) -> list[dict]:
    entity_counts: dict[str, dict] = {}
    for s in signals:
        for ent in s.get("related_entities") or []:
            key = ent
            if key not in entity_counts:
                entity_counts[key] = {"name": key, "type": "company", "count": 0}
            entity_counts[key]["count"] += 1
        for topic in s.get("related_topics") or []:
            key = topic
            if key not in entity_counts:
                entity_counts[key] = {"name": key, "type": "theme", "count": 0}
            entity_counts[key]["count"] += 1

    sorted_items = sorted(entity_counts.values(), key=lambda x: x["count"], reverse=True)
    return sorted_items[:12]


def _aggregate_source_distribution(signals: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for s in signals:
        st = s.get("source_type") or "unknown"
        counts[st] = counts.get(st, 0) + 1

    total = sum(counts.values()) or 1
    result = []
    all_sources = [
        ("official_disclosure", "官方披露"),
        ("company_ir", "公司 IR"),
        ("public_research", "公开研究"),
        ("media_excerpt", "媒体摘录"),
        ("earnings_call", "电话会纪要"),
        ("foundation", "Foundation"),
        ("risk_monitor", "风险监控"),
    ]
    for key, label in all_sources:
        count = counts.get(key, 0)
        result.append({
            "source_type": key,
            "label": label,
            "count": count,
            "pct": round(count / total * 100),
        })
    return result


def build_signal_flow_view_model(
    state: dict | None = None,
    filters: dict | None = None,
    now: datetime | None = None,
    limit: int = 20,
    backend_state: dict | None = None,
    enable_quality_gate: bool = True,
) -> dict:
    """Build the signal flow page view model from raw dashboard state.

    Always returns a valid dict, never raises.
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
        signals_data = backend_state.get("signals") or {}
        if raw_state:
            effective_state = raw_state
        elif signals_data:
            effective_state = signals_data

        page_statuses = backend_state.get("page_statuses") or {}
        if page_statuses.get("signal_flow"):
            page_data_status = page_statuses["signal_flow"]
        elif signals_data or raw_state:
            page_data_status = "real_backend"

        if page_data_status == "real_backend":
            used_real_sources = ["backend_api"]
            used_lightweight_sources = []
        else:
            missing_sources = ["backend_api"]

    state = effective_state or {}

    extraction_result = _extract_signals_from_state(state, now, enable_quality_gate=enable_quality_gate)
    raw_signals = extraction_result["signals"]
    filtered_signal_count = extraction_result.get("filtered_signal_count", 0)
    low_confidence_candidate_count = extraction_result.get("low_confidence_candidate_count", 0)

    filtered = _filter_signals(raw_signals, clean_filters, now)
    signals = filtered[:limit]

    hot_entities = _aggregate_hot_entities(filtered)
    source_distribution = _aggregate_source_distribution(filtered)

    total = len(filtered)
    focus_company_count = len({e for s in filtered for e in s.get("related_entities") or []})
    high_strength_count = sum(1 for s in filtered if s.get("evidence_strength") == "高")
    needs_review_count = sum(
        1 for s in filtered
        if s.get("review_status") in ("待复核", "待补证据")
    )

    overview = state.get("overview") or {}
    current_state = state.get("current_state") or {}
    updated_at = (
        overview.get("generated_at")
        or current_state.get("as_of")
        or now.strftime("%Y-%m-%d %H:%M")
    )

    empty_state = total == 0

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
        "summary": {
            "total_signals": total,
            "focus_company_count": focus_company_count,
            "high_strength_count": high_strength_count,
            "needs_review_count": needs_review_count,
            "filtered_signal_count": filtered_signal_count,
            "low_confidence_candidate_count": low_confidence_candidate_count,
        },
        "signals": signals,
        "hot_entities": hot_entities,
        "source_distribution": source_distribution,
        "empty_state": empty_state,
        "updated_at": updated_at,
        "strength_tones": STRENGTH_TONES,
        "source_type_labels": SOURCE_TYPE_LABELS,
        "backend_connection_summary": backend_connection_summary,
    }
