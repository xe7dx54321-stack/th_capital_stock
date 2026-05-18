#!/usr/bin/env python3
"""Helpers for prioritizing official first-party materials in downstream research flows."""

import json
from datetime import datetime

from smr_external_research import load_focus_equities

OFFICIAL_SOURCE_KEYS = (
    "official_ir_material",
    "sec_filing_document",
    "sec_earnings_material",
    "cninfo_announcement",
    "hkex_announcement",
)

HIGH_VALUE_EVENT_TYPES = {
    "earnings_call_material",
    "investor_presentation",
    "earnings_release",
    "quarterly_report",
    "annual_results_announcement",
    "interim_results_announcement",
    "investor_relations_activity",
}

EVENT_TYPE_LABELS = {
    "earnings_call_material": "电话会 / 业绩会材料",
    "investor_presentation": "演示稿",
    "earnings_release": "业绩稿 / 业绩披露",
    "quarterly_report": "季报",
    "annual_results_announcement": "年报 / 年度业绩",
    "interim_results_announcement": "中报 / 中期业绩",
    "investor_relations_activity": "投资者关系活动记录",
    "announcement_general": "官方公告",
}

SOURCE_KEY_LABELS = {
    "official_ir_material": "公司 IR 官网",
    "sec_filing_document": "SEC 主文件",
    "sec_earnings_material": "SEC 业绩附件",
    "cninfo_announcement": "巨潮资讯",
    "hkex_announcement": "港交所披露",
}

TITLE_NOISE = {
    "top of page",
    "total",
    "financial statements",
    "segment results",
    "microsoft",
    "apple",
    "alibaba group",
}


def safe_json_loads(text):
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}


def parse_ts(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def event_rank(event_type):
    order = {
        "earnings_call_material": 0,
        "earnings_release": 1,
        "investor_presentation": 2,
        "quarterly_report": 3,
        "annual_results_announcement": 4,
        "interim_results_announcement": 5,
        "investor_relations_activity": 6,
        "announcement_general": 9,
    }
    return order.get(event_type, 99)


def source_rank(source_key):
    order = {
        "official_ir_material": 0,
        "sec_earnings_material": 1,
        "sec_filing_document": 2,
        "cninfo_announcement": 3,
        "hkex_announcement": 4,
    }
    return order.get(source_key, 99)


def is_title_noise(title, source_key):
    normalized = str(title or "").strip().lower()
    if not normalized:
        return True
    if normalized in TITLE_NOISE:
        return True
    if source_key == "official_ir_material" and len(normalized) <= 4:
        return True
    return False


def include_event(source_key, event_type, title):
    normalized = str(title or "").strip().lower()
    if is_title_noise(title, source_key):
        return False
    if source_key in {"official_ir_material", "sec_filing_document", "sec_earnings_material"}:
        return event_type in HIGH_VALUE_EVENT_TYPES
    if source_key == "cninfo_announcement":
        return event_type in {"investor_relations_activity", "earnings_call_material"}
    if source_key == "hkex_announcement":
        if event_type in HIGH_VALUE_EVENT_TYPES:
            return True
        if "monthly return" in normalized or "next day disclosure" in normalized:
            return False
        if any(keyword in normalized for keyword in ("results", "presentation", "webcast", "transcript", "investor day")):
            return True
        return False
    return False


def freshness_label(latest_dt):
    if latest_dt is None:
        return "missing", None
    age_days = (datetime.now() - latest_dt).days
    if age_days <= 14:
        return "fresh_hot", age_days
    if age_days <= 45:
        return "fresh", age_days
    if age_days <= 120:
        return "usable", age_days
    return "stale", age_days


def freshness_summary(label, age_days):
    if label == "fresh_hot":
        return f"近 {age_days} 天内有很新的官方一手材料。"
    if label == "fresh":
        return f"近 {age_days} 天内有较新的官方一手材料。"
    if label == "usable":
        return f"官方一手材料距今约 {age_days} 天，仍可参考，但需要补更近更新。"
    if label == "stale":
        return f"官方一手材料距今约 {age_days} 天，已经开始变旧。"
    return "当前没有可直接复核的高价值官方一手材料。"


def latest_official_material_items(conn, ts_code, limit=5):
    rows = conn.execute(
        """
        SELECT
            source_key,
            event_type,
            title,
            publish_time,
            source_rel_path,
            payload_json
        FROM market_event
        WHERE entity_type='stock'
          AND entity_id=?
          AND source_key IN ('official_ir_material', 'sec_filing_document', 'sec_earnings_material', 'cninfo_announcement', 'hkex_announcement')
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, updated_at DESC, event_id DESC
        """,
        (ts_code,),
    ).fetchall()

    items = []
    seen = set()
    for source_key, event_type, title, publish_time, source_rel_path, payload_json in rows:
        if not include_event(source_key, event_type, title):
            continue
        dedupe_key = (source_rel_path, event_type, title)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        payload = safe_json_loads(payload_json)
        items.append(
            {
                "source_key": source_key,
                "source_label": SOURCE_KEY_LABELS.get(source_key, source_key),
                "event_type": event_type,
                "event_label": EVENT_TYPE_LABELS.get(event_type, event_type),
                "title": title,
                "publish_time": publish_time,
                "source_rel_path": source_rel_path,
                "summary": payload.get("summary"),
            }
        )

    items.sort(
        key=lambda item: (
            parse_ts(item.get("publish_time")) or datetime.min,
            -event_rank(item.get("event_type")),
            -source_rank(item.get("source_key")),
            item.get("title") or "",
        ),
        reverse=True,
    )
    return items[:limit]


def summarize_official_materials(conn, ts_code, limit=5):
    items = latest_official_material_items(conn, ts_code, limit=limit)
    latest_item = items[0] if items else None
    latest_dt = parse_ts((latest_item or {}).get("publish_time"))
    label, age_days = freshness_label(latest_dt)
    latest_date = latest_dt.strftime("%Y-%m-%d") if latest_dt else None

    if latest_item:
        summary = (
            f"{freshness_summary(label, age_days)} "
            f"最新是 {SOURCE_KEY_LABELS.get(latest_item['source_key'], latest_item['source_key'])}"
            f" 的 {EVENT_TYPE_LABELS.get(latest_item['event_type'], latest_item['event_type'])}"
            f"（{latest_date}）。"
        )
    else:
        summary = freshness_summary(label, age_days)

    return {
        "available": bool(items),
        "item_count": len(items),
        "freshness_label": label,
        "age_days": age_days,
        "summary": summary,
        "latest_title": (latest_item or {}).get("title"),
        "latest_publish_time": (latest_item or {}).get("publish_time"),
        "latest_event_type": (latest_item or {}).get("event_type"),
        "latest_source_key": (latest_item or {}).get("source_key"),
        "latest_summary": (latest_item or {}).get("summary"),
        "source_rel_paths": [item.get("source_rel_path") for item in items if item.get("source_rel_path")],
        "items": items,
    }


def load_official_material_digest(conn, limit=5, focus_ts_codes=None, fallback_to_pool=True):
    requested_codes = [ts_code for ts_code in (focus_ts_codes or []) if ts_code]
    if requested_codes:
        focus_strategy = "explicit_ts_codes"
        focus_items = load_focus_equities(conn, limit=max(limit, len(requested_codes)), focus_ts_codes=requested_codes)
    elif fallback_to_pool:
        focus_strategy = "top_pool"
        focus_items = load_focus_equities(conn, limit=limit)
    else:
        focus_strategy = "none"
        focus_items = []

    items = []
    for focus in focus_items[:limit]:
        digest = summarize_official_materials(conn, focus["ts_code"], limit=4)
        if not digest.get("available"):
            continue
        items.append(
            {
                "ts_code": focus["ts_code"],
                "name": focus["name"],
                "sector": focus["sector"],
                "pool_types": focus["pool_types"],
                "score": focus["score"],
                **digest,
            }
        )

    return {
        "focus_strategy": focus_strategy,
        "requested_focus_count": len(requested_codes),
        "focus_count": len(items),
        "focus_ts_codes": requested_codes[:limit],
        "items": items,
    }
