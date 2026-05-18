#!/usr/bin/env python3
"""Helpers for prioritizing higher-value research inputs in reporting flows."""

from datetime import datetime


SOURCE_FAMILY_PRIORITY = {
    "official_material": 400,
    "public_transcript": 300,
    "public_analyst_signal": 200,
    "external_research": 100,
}


def _parse_ts(value):
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("T", " ").replace("Z", "").split("+", 1)[0].strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized[:19], fmt)
        except ValueError:
            continue
    return None


def _recency_bonus(value, default=0):
    parsed = _parse_ts(value)
    if parsed is None:
        return default
    age_days = max((datetime.now() - parsed).days, 0)
    if age_days <= 3:
        return 60
    if age_days <= 10:
        return 35
    if age_days <= 30:
        return 15
    return 0


def _freshness_bonus(label):
    return {
        "fresh_hot": 60,
        "fresh": 45,
        "usable": 20,
        "stale": 0,
        "missing": -20,
        "not_applicable": -40,
    }.get(str(label or "").strip().lower(), 0)


def _analyst_stance_bonus(label):
    return {
        "supportive_strong": 35,
        "supportive": 24,
        "neutral_watch": 10,
        "neutral": 0,
        "stretched": -8,
        "cautious": -18,
        "missing": -25,
        "not_applicable": -40,
    }.get(str(label or "").strip().lower(), 0)


def _external_research_bonus(item):
    bonus = _recency_bonus(item.get("published_at") or item.get("updated_at"))
    if item.get("target_price_yuan") not in (None, "", "-", "--"):
        bonus += 8
    if item.get("rating_name"):
        bonus += 4
    return bonus


def _official_bonus(item):
    bonus = _freshness_bonus(item.get("freshness_label"))
    bonus += min(int(item.get("item_count") or 0), 4) * 4
    return bonus


def _transcript_bonus(item):
    bonus = _freshness_bonus(item.get("freshness_label"))
    bonus += min(int(item.get("speaker_count") or 0), 6)
    return bonus


def _public_signal_bonus(item):
    bonus = _freshness_bonus(item.get("freshness_label"))
    bonus += _analyst_stance_bonus(item.get("stance_label"))
    spread = item.get("spread_avg_target_pct")
    if spread is not None:
        bonus += max(min(float(spread), 20.0), -20.0) / 2.0
    return round(bonus, 2)


def _source_rel_paths(item):
    values = []
    for value in (item.get("source_rel_paths") or []):
        text = str(value or "").strip()
        if text and text not in values:
            values.append(text)
    single = str(item.get("source_rel_path") or "").strip()
    if single and single not in values:
        values.append(single)
    return values


def _base_entry(item, source_family, priority_score, headline, summary):
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "source_family": source_family,
        "priority_score": round(priority_score, 2),
        "headline": headline,
        "summary": summary,
        "provider": item.get("provider"),
        "latest_at": item.get("latest_publish_time") or item.get("published_at") or item.get("updated_at"),
        "source_rel_paths": _source_rel_paths(item),
    }


def build_high_value_reporting_digest(
    external_research_digest,
    official_material_digest,
    public_transcript_digest,
    public_analyst_signal_digest,
    limit=12,
):
    items = []

    for item in (official_material_digest or {}).get("items") or []:
        priority_score = SOURCE_FAMILY_PRIORITY["official_material"] + _official_bonus(item)
        headline = item.get("summary") or item.get("latest_title") or "官方一手材料已更新。"
        items.append(
            _base_entry(
                item,
                "official_material",
                priority_score,
                headline,
                item.get("summary") or headline,
            )
        )

    for item in (public_transcript_digest or {}).get("items") or []:
        priority_score = SOURCE_FAMILY_PRIORITY["public_transcript"] + _transcript_bonus(item)
        headline = item.get("summary") or "公开电话会文字稿可用于核对管理层原话。"
        items.append(
            _base_entry(
                item,
                "public_transcript",
                priority_score,
                headline,
                headline,
            )
        )

    for item in (public_analyst_signal_digest or {}).get("items") or []:
        priority_score = SOURCE_FAMILY_PRIORITY["public_analyst_signal"] + _public_signal_bonus(item)
        headline = item.get("summary") or "公开卖方信号可作为辅助参照。"
        items.append(
            _base_entry(
                item,
                "public_analyst_signal",
                priority_score,
                headline,
                headline,
            )
        )

    for item in (external_research_digest or {}).get("items") or []:
        priority_score = SOURCE_FAMILY_PRIORITY["external_research"] + _external_research_bonus(item)
        published_at = item.get("published_at") or item.get("updated_at") or "-"
        headline = (
            f"{item.get('org_name') or '外部机构'} {item.get('rating_name') or '研究'} / "
            f"{published_at[:10] if isinstance(published_at, str) else published_at}"
        )
        items.append(
            _base_entry(
                item,
                "external_research",
                priority_score,
                headline,
                headline,
            )
        )

    items.sort(
        key=lambda item: (
            -(item.get("priority_score") or 0),
            item.get("latest_at") or "",
            item.get("ts_code") or "",
            item.get("source_family") or "",
        )
    )

    return {
        "priority_rule": "official_material > public_transcript > public_analyst_signal > external_research",
        "focus_count": len(items[:limit]),
        "items": items[:limit],
    }
