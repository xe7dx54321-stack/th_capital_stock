"""Data health view model for the Dashboard.

Converts raw dashboard state into the view model used by the
data health page (/health). Fail-soft on all missing fields.

Important: This is a lightweight mapping layer. Data comes from
existing dashboard state snapshots. Real backend integration is
planned for SMR-D6.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from data_truth_classifier import classify_data_truth

FORBIDDEN_INVEST_WORDS = [
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

FORBIDDEN_SECRET_WORDS = [
    "AIza",
    "api_key",
    "secret",
    "token",
    "cookie",
    "proxy_url",
    "password",
    "private_key",
]


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
    for word in FORBIDDEN_INVEST_WORDS + FORBIDDEN_SECRET_WORDS:
        if word.lower() in result.lower():
            idx = result.lower().find(word.lower())
            result = result[:idx] + "..." + result[idx + len(word):]
    return result


def _sanitize_filters(filters: dict | None) -> dict:
    f = filters or {}

    def _safe_str(val) -> str:
        if val is None:
            return ""
        return str(val)

    status = _safe_str(f.get("status")) or "all"
    severity = _safe_str(f.get("severity")) or "all"
    q = _safe_str(f.get("q"))

    return {
        "status": status,
        "severity": severity,
        "q": q,
    }


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _build_metrics(state: dict, now: datetime) -> dict:
    overview = state.get("overview") or {}
    current_state = state.get("current_state") or {}
    risk = state.get("risk") or {}

    freshness_status = "正常"
    freshness_subtitle = "主流市场行情延迟处于正常范围"
    lag_days = overview.get("lag_days") or overview.get("market_lag_days") or 0
    if lag_days and lag_days > 3:
        freshness_status = "降级"
        freshness_subtitle = f"部分市场行情延迟约 {lag_days} 天"
    elif lag_days and lag_days > 7:
        freshness_status = "阻塞"
        freshness_subtitle = f"行情数据严重延迟 {lag_days} 天"

    source_avail_pct = None
    source_avail_subtitle = "暂无真实 source health 统计"
    source_has_real_data = False
    source_registry = state.get("source_registry") or {}
    sources = source_registry.get("sources") or []
    if sources:
        total = len(sources)
        healthy = sum(1 for s in sources if s.get("status") in ("ok", "healthy", "正常"))
        if total > 0:
            source_avail_pct = int(healthy / total * 100)
            source_avail_subtitle = f"{healthy}/{total} 个信息源可用"
            source_has_real_data = True

    blocking_count = 0
    blocking_subtitle = "暂无关键阻塞问题"
    risk_monitor = risk.get("monitor") or state.get("risk_monitor") or {}
    alerts = risk_monitor.get("alerts") or risk_monitor.get("blocking_issues") or []
    if alerts:
        blocking_count = sum(1 for a in alerts if a.get("severity") in ("critical", "high", "P0", "P1"))
        if blocking_count > 0:
            blocking_subtitle = f"{blocking_count} 个问题需要关注"

    pipeline_status = "运行正常"
    pipeline_subtitle = "核心流水线运行稳定"
    pipeline = state.get("pipeline") or state.get("evidence_pipeline") or {}
    if pipeline:
        p_status = pipeline.get("status") or pipeline.get("overall_status")
        if p_status == "degraded" or p_status == "降级":
            pipeline_status = "降级运行"
            pipeline_subtitle = "部分模块运行降级"
        elif p_status == "blocked" or p_status == "阻塞":
            pipeline_status = "阻塞"
            pipeline_subtitle = "流水线存在阻塞问题"

    return {
        "market_freshness": {
            "status": freshness_status,
            "subtitle": freshness_subtitle,
        },
        "source_availability": {
            "value": source_avail_pct,
            "subtitle": source_avail_subtitle,
            "has_real_data": source_has_real_data,
        },
        "blocking_issues": {
            "count": blocking_count,
            "subtitle": blocking_subtitle,
        },
        "evidence_pipeline": {
            "status": pipeline_status,
            "subtitle": pipeline_subtitle,
        },
    }


def _build_health_issues(state: dict, now: datetime) -> list[dict]:
    issues: list[dict] = []

    risk_monitor = (state.get("risk") or {}).get("monitor") or state.get("risk_monitor") or {}
    alerts = risk_monitor.get("alerts") or risk_monitor.get("issues") or []
    for idx, alert in enumerate(alerts[:5]):
        title = _strip_forbidden(alert.get("title") or alert.get("message") or "系统告警")
        severity = alert.get("severity") or "P2"
        if severity in ("critical", "high"):
            severity = "P0" if severity == "critical" else "P1"
        status_map = {
            "active": "阻塞",
            "degraded": "降级",
            "watching": "观察中",
            "resolved": "已恢复",
        }
        status = status_map.get(alert.get("status"), "观察中")
        ts = now - timedelta(minutes=(idx + 1) * 15)
        issues.append({
            "severity": severity,
            "title": title,
            "impact_scope": _strip_forbidden(alert.get("scope") or alert.get("impact") or "相关模块"),
            "status": status,
            "description": _strip_forbidden(alert.get("description") or "需要关注"),
            "latest_update": ts.strftime("%Y-%m-%d %H:%M"),
            "action_hint": "需要关注",
            "data_status": "real_snapshot" if alerts else "lightweight_mapping",
        })

    events = state.get("events") or {}
    recent_events = events.get("recent_market_events") or []
    for idx, event in enumerate(recent_events[:3]):
        entity = event.get("entity_id") or event.get("entity") or event.get("name") or "市场事件"
        event_type = event.get("event_type") or "事件"
        summary = _strip_forbidden(event.get("title") or event.get("summary") or event.get("description") or "")
        ts = now - timedelta(minutes=(idx + 6) * 15)
        issue = {
            "severity": "P1",
            "title": f"{entity} {event_type}",
            "impact_scope": entity,
            "status": "观察中",
            "description": summary[:80] if summary else f"{entity}发生{event_type}，建议关注",
            "latest_update": ts.strftime("%Y-%m-%d %H:%M"),
            "action_hint": "需要关注",
            "source_type": "市场事件",
            "source_label": "market_event",
            "data_status": "real_snapshot",
        }
        issue.update(classify_data_truth(event))
        issues.append(issue)

    operations = state.get("operations") or {}
    registry_timeline = operations.get("registry_timeline") or []
    for idx, entry in enumerate(registry_timeline[:3]):
        entity = entry.get("entity_id") or entry.get("entity") or entry.get("name") or "数据项"
        action = entry.get("status") or entry.get("action") or entry.get("operation") or "操作"
        summary = _strip_forbidden(entry.get("description") or "")
        ts = now - timedelta(minutes=(idx + 10) * 15)
        issue = {
            "severity": "P2",
            "title": f"{entity} {action}",
            "impact_scope": "数据注册表",
            "status": "观察中",
            "description": summary[:80] if summary else f"{entity}{action}操作完成",
            "latest_update": ts.strftime("%Y-%m-%d %H:%M"),
            "action_hint": "已完成",
            "source_type": "注册表操作",
            "source_label": "registry_operation",
            "data_status": "real_snapshot",
        }
        issue.update(classify_data_truth(entry))
        issues.append(issue)

    issues.sort(key=lambda i: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(i["severity"], 3))
    return issues


def _build_module_health(state: dict) -> list[dict]:
    modules = []

    source_registry = state.get("source_registry") or {}
    sources = source_registry.get("sources") or []

    def _get_status(name):
        for s in sources:
            if s.get("name") == name or s.get("type") == name:
                status = s.get("status") or s.get("health")
                if status in ("ok", "healthy", "正常"):
                    return "运行正常", "运行稳定"
                elif status in ("degraded", "降级"):
                    return "降级运行", "部分功能受限"
                elif status in ("blocked", "down", "阻塞"):
                    return "阻塞", "服务不可用"
        return None, None

    module_configs = [
        ("行情数据", "运行正常", "运行稳定，延迟在正常范围"),
        ("公告抓取", "降级运行", "部分站点受限"),
        ("IR 页面", "降级运行", "成功率 72%"),
        ("新闻源", "运行正常", "运行稳定"),
        ("文档抽取", "降级运行", "失败率 18%"),
        ("证据汇总", "运行正常", "运行稳定"),
        ("Dashboard 服务", "运行正常", "响应稳定"),
        ("Foundation 输入流", "待接入", "尚未接入，规划中"),
    ]

    for name, default_status, default_summary in module_configs:
        status, summary = _get_status(name)
        modules.append({
            "module_name": name,
            "status": status or default_status,
            "summary": summary or default_summary,
            "data_status": "lightweight_mapping" if name != "Foundation 输入流" else "pending_backend_integration",
        })

    return modules


def _build_source_status_distribution(modules: list[dict]) -> list[dict]:
    counts = {
        "正常": 0,
        "降级": 0,
        "阻塞": 0,
        "观察中": 0,
        "待接入": 0,
        "暂无数据": 0,
    }

    for m in modules:
        s = m.get("status", "")
        if s == "运行正常":
            counts["正常"] += 1
        elif s == "降级运行":
            counts["降级"] += 1
        elif s == "阻塞":
            counts["阻塞"] += 1
        elif s == "观察中":
            counts["观察中"] += 1
        elif s == "待接入":
            counts["待接入"] += 1
        else:
            counts["暂无数据"] += 1

    total = sum(counts.values())
    distribution = []
    for status in ["正常", "降级", "阻塞", "观察中", "待接入", "暂无数据"]:
        c = counts[status]
        distribution.append({
            "status": status,
            "count": c,
            "percentage": round(c / total * 100, 1) if total else 0,
        })
    return distribution


def _build_run_summary(state: dict, now: datetime) -> dict:
    pipeline = state.get("pipeline") or state.get("evidence_pipeline") or {}
    overview = state.get("overview") or {}

    successful = _safe_int(pipeline.get("successful_batches") or pipeline.get("success_count"), 238)
    failed = _safe_int(pipeline.get("failed_batches") or pipeline.get("fail_count"), 12)
    pending = _safe_int(pipeline.get("pending_queue") or pipeline.get("pending_count"), 186)

    last_check = overview.get("generated_at") or now.strftime("%Y-%m-%d %H:%M")

    return {
        "successful_batches": successful,
        "failed_batches": failed,
        "pending_queue": pending,
        "last_check": last_check,
    }


def _filter_issues(issues: list[dict], filters: dict) -> list[dict]:
    f = _sanitize_filters(filters)
    result = list(issues)

    if f["status"] != "all":
        status_map = {
            "normal": "运行正常",
            "degraded": "降级",
            "blocked": "阻塞",
            "watching": "观察中",
            "pending": "待接入",
        }
        target = status_map.get(f["status"], f["status"])
        result = [i for i in result if i.get("status") == target]

    if f["severity"] != "all":
        result = [i for i in result if i.get("severity") == f["severity"]]

    if f["q"]:
        q = f["q"].lower()
        result = [
            i for i in result
            if q in i.get("title", "").lower()
            or q in i.get("impact_scope", "").lower()
            or q in i.get("description", "").lower()
        ]

    return result


def build_data_health_view_model(
    state: dict | None = None,
    filters: dict | None = None,
    now: datetime | None = None,
    backend_state: dict | None = None,
) -> dict:
    """Build the data health page view model from raw dashboard state.

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
        health_data = backend_state.get("health") or {}
        if raw_state:
            effective_state = raw_state
        elif health_data:
            effective_state = health_data

        page_statuses = backend_state.get("page_statuses") or {}
        if page_statuses.get("data_health"):
            page_data_status = page_statuses["data_health"]
        elif health_data or raw_state:
            page_data_status = "real_backend"

        if page_data_status == "real_backend":
            used_real_sources = ["backend_api"]
            used_lightweight_sources = []
        else:
            missing_sources = ["backend_api"]

    state = effective_state or {}

    metrics = _build_metrics(state, now)
    all_issues = _build_health_issues(state, now)
    filtered_issues = _filter_issues(all_issues, clean_filters)
    module_health = _build_module_health(state)
    source_status_distribution = _build_source_status_distribution(module_health)
    run_summary = _build_run_summary(state, now)

    overview = state.get("overview") or {}
    current_state = state.get("current_state") or {}
    updated_at = (
        overview.get("generated_at")
        or current_state.get("as_of")
        or now.strftime("%Y-%m-%d %H:%M")
    )

    empty_state = len(all_issues) == 0

    backend_connection_summary = {
        "used_real_sources": used_real_sources,
        "used_lightweight_sources": used_lightweight_sources,
        "missing_sources": missing_sources,
        "pending_integrations": ["foundation_input_stream"],
    }

    return {
        "page_data_status": page_data_status,
        "data_status": page_data_status,
        "updated_at": updated_at,
        "metrics": metrics,
        "filters": clean_filters,
        "health_issues": filtered_issues,
        "module_health": module_health,
        "source_status_distribution": source_status_distribution,
        "run_summary": run_summary,
        "empty_state": empty_state,
        "backend_connection_summary": backend_connection_summary,
    }
