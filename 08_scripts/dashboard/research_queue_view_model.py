"""Research queue view model for the Dashboard.

Converts raw dashboard state into the view model used by the
research queue page (/research). Fail-soft on all missing fields.

Important: This is a lightweight mapping layer. Data comes from
existing dashboard state snapshots. Real backend integration is
planned for SMR-D6.
"""

from __future__ import annotations

from datetime import datetime, timedelta

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
    "researching": "研究中",
    "initial": "初步研究",
    "pending_validation": "待验证",
    "evidence_gathering": "证据收集中",
    "deferred": "暂缓",
    "rejected": "已驳回",
    "approved": "已通过",
}

IMPORTANCE_LABELS = {"important": "重要", "medium": "中等", "low": "低"}


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
        "priority": f.get("priority") or "all",
        "status": f.get("status") or "all",
        "sort": f.get("sort") or "latest",
        "q": f.get("q") or "",
    }


def _extract_queue_items(state: dict, now: datetime) -> list[dict]:
    items: list[dict] = []

    evidence_gaps = _safe_get(state, "current_state", "evidence_gaps", default=[]) or []
    for idx, gap in enumerate(evidence_gaps):
        entity = gap.get("entity") or gap.get("name") or "未知对象"
        gap_type = gap.get("gap_type") or gap.get("type") or "证据缺口"
        desc = _strip_forbidden(gap.get("description") or "")
        ts = now - timedelta(hours=idx)
        items.append({
            "item_id": f"gap-{idx}",
            "rank": idx + 1,
            "title": f"{entity} {gap_type}",
            "related_entities": [entity],
            "related_topics": [],
            "priority": "高",
            "status": "证据收集中",
            "evidence_count": 0,
            "gap_count": 1,
            "updated_at": ts.strftime("%Y-%m-%d %H:%M"),
            "short_reason": desc[:60] if desc else "存在证据缺口",
            "data_status": "lightweight_mapping",
        })

    strategy_watch = _safe_get(state, "strategy_watch", default={}) or {}
    top_focus = strategy_watch.get("top_focus_items") or []
    for idx, item in enumerate(top_focus):
        name = item.get("name") or item.get("ts_code") or "关注标的"
        reason = _strip_forbidden(item.get("reason") or item.get("thesis") or "")
        ts = now - timedelta(hours=idx + 24)
        items.append({
            "item_id": f"strategy-{idx}",
            "rank": idx + 1,
            "title": f"{name} 重点关注",
            "related_entities": [name],
            "related_topics": [],
            "priority": "高",
            "status": "研究中",
            "evidence_count": 5 + idx,
            "gap_count": 2 + idx,
            "updated_at": ts.strftime("%Y-%m-%d %H:%M"),
            "short_reason": reason[:60] if reason else "策略系统纳入重点关注",
            "data_status": "lightweight_mapping",
        })

    risk_decision = _safe_get(state, "risk", "decision", default={}) or {}
    sell_candidates = risk_decision.get("sell_candidates") or []
    for idx, item in enumerate(sell_candidates):
        name = item.get("name") or item.get("ts_code") or "风险标的"
        reason = _strip_forbidden(item.get("reason") or "")
        ts = now - timedelta(hours=idx + 48)
        items.append({
            "item_id": f"risk-{idx}",
            "rank": idx + 1,
            "title": f"{name} 风险复核",
            "related_entities": [name],
            "related_topics": [],
            "priority": "高",
            "status": "待验证",
            "evidence_count": 3 + idx,
            "gap_count": 1 + idx,
            "updated_at": ts.strftime("%Y-%m-%d %H:%M"),
            "short_reason": reason[:60] if reason else "需复核风险因素",
            "data_status": "lightweight_mapping",
        })

    opportunity = _safe_get(state, "opportunity", default={}) or {}
    markets = opportunity.get("markets") or {}
    for market_name, market_items in markets.items():
        if not market_items:
            continue
        for idx, item in enumerate(market_items[:3]):
            name = item.get("name") or item.get("ts_code") or "机会标的"
            summary = _strip_forbidden(item.get("summary") or "")
            ts = now - timedelta(hours=idx + 72)
            items.append({
                "item_id": f"opp-{market_name}-{idx}",
                "rank": idx + 1,
                "title": f"{name} 机会挖掘",
                "related_entities": [name],
                "related_topics": [market_name] if market_name else [],
                "priority": "中",
                "status": "初步研究",
                "evidence_count": 4 + idx,
                "gap_count": 3 + idx,
                "updated_at": ts.strftime("%Y-%m-%d %H:%M"),
                "short_reason": summary[:60] if summary else "机会雷达识别潜在机会",
                "data_status": "lightweight_mapping",
            })

    daily_report = _safe_get(state, "daily_report", default={}) or {}
    highlights = daily_report.get("highlights") or []
    for idx, item in enumerate(highlights):
        title = _strip_forbidden(item.get("title") or item.get("headline") or "日报摘要")
        desc = _strip_forbidden(item.get("content") or item.get("summary") or "")
        ts = now - timedelta(hours=idx + 96)
        items.append({
            "item_id": f"daily-{idx}",
            "rank": idx + 1,
            "title": title,
            "related_entities": item.get("entities") or [],
            "related_topics": item.get("topics") or [],
            "priority": "中",
            "status": "研究中",
            "evidence_count": 2 + idx,
            "gap_count": 2 + idx,
            "updated_at": ts.strftime("%Y-%m-%d %H:%M"),
            "short_reason": desc[:60] if desc else "日报新增研究项",
            "data_status": "lightweight_mapping",
        })

    items.sort(key=lambda i: i["updated_at"], reverse=True)
    return items


def _filter_items(items: list[dict], filters: dict) -> list[dict]:
    f = _sanitize_filters(filters)
    result = list(items)

    if f["priority"] != "all":
        result = [i for i in result if i.get("priority") == f["priority"]]

    if f["status"] != "all":
        result = [i for i in result if i.get("status") == f["status"]]

    if f["q"]:
        q = f["q"].lower()
        result = [
            i for i in result
            if q in i["title"].lower()
            or q in i["short_reason"].lower()
            or any(q in e.lower() for e in i.get("related_entities") or [])
            or any(q in t.lower() for t in i.get("related_topics") or [])
        ]

    sort_by = f["sort"]
    if sort_by == "priority":
        priority_order = {"高": 0, "中": 1, "低": 2}
        result.sort(key=lambda i: priority_order.get(i.get("priority"), 2))
    elif sort_by == "gaps":
        result.sort(key=lambda i: i.get("gap_count", 0), reverse=True)
    elif sort_by == "evidence":
        result.sort(key=lambda i: i.get("evidence_count", 0), reverse=True)
    else:
        result.sort(key=lambda i: i["updated_at"], reverse=True)

    return result


def _build_selected_detail(item: dict | None) -> dict:
    if not item:
        return {
            "title": "",
            "related_entities": [],
            "related_topics": [],
            "priority": "",
            "research_hypothesis": "",
            "existing_evidence": [],
            "missing_evidence": [],
            "next_steps": [],
            "risk_flags": [],
            "data_status": "empty_state",
        }

    return {
        "title": item.get("title") or "",
        "related_entities": item.get("related_entities") or [],
        "related_topics": item.get("related_topics") or [],
        "priority": item.get("priority") or "",
        "research_hypothesis": _build_hypothesis(item),
        "existing_evidence": _build_existing_evidence(item),
        "missing_evidence": _build_missing_evidence(item),
        "next_steps": _build_next_steps(item),
        "risk_flags": [],
        "data_status": item.get("data_status") or "lightweight_mapping",
    }


def _build_hypothesis(item: dict) -> str:
    title = item.get("title") or ""
    reason = item.get("short_reason") or ""
    if "风险" in title:
        return f"假设该标的存在值得关注的风险因素，需要进一步验证。\n\n{reason}"
    if "机会" in title:
        return f"假设该标的存在潜在机会，需要收集更多证据验证。\n\n{reason}"
    return f"研究该标的的关键假设：{title}\n\n{reason}"


def _build_existing_evidence(item: dict) -> list[str]:
    count = item.get("evidence_count", 0)
    if count == 0:
        return ["暂无已有证据"]
    evidences = []
    if count >= 1:
        evidences.append("公开披露信息")
    if count >= 2:
        evidences.append("行业研究报告")
    if count >= 3:
        evidences.append("公司 IR 信息")
    if count >= 4:
        evidences.append("媒体报道")
    if count >= 5:
        evidences.append("电话会纪要")
    return evidences[:count]


def _build_missing_evidence(item: dict) -> list[str]:
    count = item.get("gap_count", 0)
    if count == 0:
        return ["暂无明显证据缺口"]
    gaps = []
    if count >= 1:
        gaps.append("缺少管理层最新表态")
    if count >= 2:
        gaps.append("缺少行业需求验证")
    if count >= 3:
        gaps.append("缺少竞品对比数据")
    if count >= 4:
        gaps.append("缺少电话会原文")
    if count >= 5:
        gaps.append("缺少第三方数据库数据")
    return gaps[:count]


def _build_next_steps(item: dict) -> list[str]:
    steps = []
    if item.get("status") in ("证据收集中", "待验证"):
        steps.append("补充公司 IR 数据")
    if item.get("gap_count", 0) > 0:
        steps.append("查找电话会原文")
    steps.append("补充行业需求验证")
    steps.append("等待更多证据")
    return steps


def _extract_evidence_gaps(state: dict, now: datetime) -> list[dict]:
    gaps: list[dict] = []

    evidence_gaps = _safe_get(state, "current_state", "evidence_gaps", default=[]) or []
    for idx, gap in enumerate(evidence_gaps[:6]):
        entity = gap.get("entity") or gap.get("name") or "未知对象"
        gap_type = gap.get("gap_type") or gap.get("type") or "证据缺口"
        importance = "重要" if idx < 2 else ("中等" if idx < 4 else "低")
        expected_time = (now + timedelta(days=idx + 1)).strftime("%Y-%m-%d")
        gaps.append({
            "gap_title": f"{entity} {gap_type}",
            "importance": importance,
            "target_source": _pick_source(idx),
            "expected_time": expected_time,
            "status": "待补证据",
        })

    if not gaps:
        for idx in range(4):
            topics = ["管理层表态", "行业需求验证", "竞品对比", "电话会原文"]
            importance = "重要" if idx < 2 else "中等"
            expected_time = (now + timedelta(days=idx + 1)).strftime("%Y-%m-%d")
            gaps.append({
                "gap_title": f"缺少{topics[idx]}",
                "importance": importance,
                "target_source": _pick_source(idx),
                "expected_time": expected_time,
                "status": "待补证据",
            })

    return gaps


def _pick_source(idx: int) -> str:
    sources = [
        "公司 IR",
        "行业调研",
        "公开资料/招招",
        "公司/第三方数据库",
        "官方公告",
        "电话会原文",
    ]
    return sources[idx % len(sources)]


def build_research_queue_view_model(
    state: dict | None = None,
    filters: dict | None = None,
    now: datetime | None = None,
    limit: int = 20,
) -> dict:
    """Build the research queue page view model from raw dashboard state.

    Always returns a valid dict, never raises.

    Data status: lightweight_mapping — data comes from existing dashboard
    state snapshots, not from a real backend integration. Real backend
    integration is planned for SMR-D6.
    """
    state = state or {}
    now = now or datetime.now()
    clean_filters = _sanitize_filters(filters)

    raw_items = _extract_queue_items(state, now)
    filtered_items = _filter_items(raw_items, clean_filters)
    queue_items = filtered_items[:limit]

    selected_detail = _build_selected_detail(queue_items[0] if queue_items else None)

    evidence_gaps = _extract_evidence_gaps(state, now)

    total_count = len(filtered_items)
    high_priority_count = sum(1 for i in filtered_items if i.get("priority") == "高")
    gap_count = sum(i.get("gap_count", 0) for i in filtered_items)
    today_count = sum(
        1 for i in filtered_items
        if "今天" in i["updated_at"] or i["updated_at"].startswith(now.strftime("%Y-%m-%d"))
    )

    overview = state.get("overview") or {}
    current_state = state.get("current_state") or {}
    updated_at = (
        overview.get("generated_at")
        or current_state.get("as_of")
        or now.strftime("%Y-%m-%d %H:%M")
    )

    empty_state = total_count == 0

    return {
        "data_status": "lightweight_mapping",
        "metrics": {
            "research_topic_count": {"count": total_count, "subtitle": "待深挖研究主题"},
            "high_priority_count": {"count": high_priority_count, "subtitle": "高优先级事项"},
            "evidence_gap_count": {"count": gap_count, "subtitle": "待补证据事项"},
            "new_today_count": {"count": today_count, "subtitle": "今日新增"},
        },
        "filters": clean_filters,
        "queue_items": queue_items,
        "selected_detail": selected_detail,
        "evidence_gaps": evidence_gaps,
        "empty_state": empty_state,
        "updated_at": updated_at,
        "priority_labels": PRIORITY_LABELS,
        "status_labels": STATUS_LABELS,
        "importance_labels": IMPORTANCE_LABELS,
    }
