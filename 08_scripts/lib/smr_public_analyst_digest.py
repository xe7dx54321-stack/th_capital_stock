#!/usr/bin/env python3
"""Helpers for loading latest public analyst-signal digests into downstream payloads."""

import json
from datetime import datetime

from smr_external_research import load_focus_equities
from smr_paths import project_path
from smr_wiki import ensure_source_manifest_table


def parse_metadata_json(text):
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}


def load_json_rel_path(rel_path):
    if not rel_path:
        return None
    path = project_path(rel_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def summarize_item(meta_payload):
    mean_consensus = meta_payload.get("mean_consensus")
    analysts_count = meta_payload.get("analysts_count")
    spread_avg_target_pct = meta_payload.get("spread_avg_target_pct")
    average_target_raw = meta_payload.get("average_target_raw")
    last_close_raw = meta_payload.get("last_close_raw")
    summary_parts = []
    if mean_consensus:
        summary_parts.append(f"公开一致预期为 {mean_consensus}")
    if analysts_count:
        summary_parts.append(f"覆盖分析师约 {analysts_count} 家")
    if average_target_raw:
        summary_parts.append(f"平均目标价 {average_target_raw}")
    if spread_avg_target_pct is not None:
        sign = "+" if spread_avg_target_pct > 0 else ""
        summary_parts.append(f"相对现价空间 {sign}{spread_avg_target_pct:.2f}%")
    if last_close_raw:
        summary_parts.append(f"现价参考 {last_close_raw}")
    return "，".join(summary_parts) if summary_parts else "当前暂无可用的公开卖方信号摘要。"


def parse_date_prefix(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def supports_public_analyst_signal(ts_code):
    text = str(ts_code or "").upper()
    return bool(text) and not text.endswith((".SZ", ".SH", ".BJ"))


def signal_freshness_label(published_at):
    published_dt = parse_date_prefix(published_at)
    if published_dt is None:
        return "missing", None
    age_days = (datetime.now() - published_dt).days
    if age_days <= 3:
        return "fresh", age_days
    if age_days <= 10:
        return "usable", age_days
    return "stale", age_days


def consensus_bucket(mean_consensus):
    text = str(mean_consensus or "").strip().upper()
    if text in {"BUY", "STRONG BUY", "OUTPERFORM", "OVERWEIGHT", "ACCUMULATE"}:
        return "positive"
    if text in {"HOLD", "NEUTRAL", "MARKET PERFORM", "EQUAL-WEIGHT"}:
        return "neutral"
    if text in {"SELL", "UNDERPERFORM", "UNDERWEIGHT", "REDUCE"}:
        return "negative"
    return "unknown"


def signal_stance(snapshot):
    consensus_type = consensus_bucket(snapshot.get("mean_consensus"))
    spread = snapshot.get("spread_avg_target_pct")

    if spread is None:
        return "neutral", "公开卖方有覆盖，但当前拿不到明确目标价空间。"
    if consensus_type == "negative" or spread <= -10:
        return "cautious", "公开卖方口径已经偏谨慎，平均目标价明显低于现价。"
    if spread < 0:
        return "stretched", "公开卖方仍有覆盖，但平均目标价已经低于现价，市场可能先走在预期前面。"
    if consensus_type == "positive" and spread >= 20:
        return "supportive_strong", "公开卖方口径偏积极，而且平均目标价仍有较明显上行空间。"
    if consensus_type == "positive" and spread >= 8:
        return "supportive", "公开卖方口径偏积极，平均目标价相对现价仍有一定空间。"
    if consensus_type == "neutral" and spread >= 10:
        return "neutral_watch", "公开卖方没有明显唱多，但目标价空间仍提示值得继续跟踪。"
    return "neutral", "公开卖方口径中性，更多适合作为辅助参照。"


def enrich_snapshot(snapshot):
    if not snapshot:
        return None
    freshness_label, freshness_age_days = signal_freshness_label(snapshot.get("published_at"))
    stance_label, stance_summary = signal_stance(snapshot)
    summary = summarize_item(snapshot)
    return {
        **snapshot,
        "freshness_label": freshness_label,
        "freshness_age_days": freshness_age_days,
        "stance_label": stance_label,
        "stance_summary": stance_summary,
        "summary": f"{summary}。{stance_summary}",
    }


def summarize_public_analyst_signal(conn, ts_code):
    snapshot = latest_public_analyst_signal_snapshot(conn, ts_code)
    if not snapshot:
        if not supports_public_analyst_signal(ts_code):
            return {
                "available": False,
                "item_count": 0,
                "freshness_label": "not_applicable",
                "freshness_age_days": None,
                "stance_label": "not_applicable",
                "stance_summary": "当前市场暂不适用这条公开卖方参照链路。",
                "summary": "当前市场暂不适用这条公开卖方参照链路。",
                "source_rel_path": None,
                "source_rel_paths": [],
                "provider": None,
                "published_at": None,
                "snapshot_date": None,
                "mean_consensus": None,
                "analysts_count": None,
                "average_target_raw": None,
                "last_close_raw": None,
                "spread_avg_target_pct": None,
            }
        return {
            "available": False,
            "item_count": 0,
            "freshness_label": "missing",
            "freshness_age_days": None,
            "stance_label": "missing",
            "stance_summary": "当前没有可直接参考的公开卖方信号摘要。",
            "summary": "当前没有可直接参考的公开卖方信号摘要。",
            "source_rel_path": None,
            "source_rel_paths": [],
            "provider": None,
            "published_at": None,
            "snapshot_date": None,
            "mean_consensus": None,
            "analysts_count": None,
            "average_target_raw": None,
            "last_close_raw": None,
            "spread_avg_target_pct": None,
        }
    return {
        "available": True,
        "item_count": 1,
        "source_rel_paths": [snapshot.get("source_rel_path")] if snapshot.get("source_rel_path") else [],
        **snapshot,
    }


def latest_public_analyst_signal_snapshot(conn, ts_code):
    ensure_source_manifest_table(conn)
    rows = conn.execute(
        """
        SELECT title, source_rel_path, metadata_json, updated_at
        FROM source_manifest
        WHERE status='active'
          AND source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')='public_analyst_signal'
        ORDER BY datetime(updated_at) DESC, source_id DESC
        LIMIT 4
        """,
        (ts_code,),
    ).fetchall()

    for title, source_rel_path, metadata_json, updated_at in rows:
        metadata = parse_metadata_json(metadata_json)
        meta_payload = load_json_rel_path(metadata.get("meta_rel_path"))
        if not meta_payload:
            continue
        return enrich_snapshot(
            {
            "source_kind": "public_analyst_signal",
            "provider": meta_payload.get("provider") or "marketscreener",
            "title": title,
            "source_rel_path": source_rel_path,
            "updated_at": updated_at,
            "published_at": meta_payload.get("published_at"),
            "snapshot_date": meta_payload.get("snapshot_date"),
            "mean_consensus": meta_payload.get("mean_consensus"),
            "analysts_count": meta_payload.get("analysts_count"),
            "last_close_price": meta_payload.get("last_close_price"),
            "last_close_currency": meta_payload.get("last_close_currency"),
            "last_close_raw": meta_payload.get("last_close_raw"),
            "average_target_price": meta_payload.get("average_target_price"),
            "average_target_currency": meta_payload.get("average_target_currency"),
            "average_target_raw": meta_payload.get("average_target_raw"),
            "spread_avg_target_pct": meta_payload.get("spread_avg_target_pct"),
            "high_target_price": meta_payload.get("high_target_price"),
            "high_target_currency": meta_payload.get("high_target_currency"),
            "high_target_raw": meta_payload.get("high_target_raw"),
            "spread_high_target_pct": meta_payload.get("spread_high_target_pct"),
            "low_target_price": meta_payload.get("low_target_price"),
            "low_target_currency": meta_payload.get("low_target_currency"),
            "low_target_raw": meta_payload.get("low_target_raw"),
            "spread_low_target_pct": meta_payload.get("spread_low_target_pct"),
            }
        )
    return None


def latest_public_analyst_signal_items(conn, limit=7):
    ensure_source_manifest_table(conn)
    rows = conn.execute(
        """
        SELECT entity_id, title, source_rel_path, metadata_json, updated_at
        FROM (
            SELECT
                entity_id,
                title,
                source_rel_path,
                metadata_json,
                updated_at,
                source_id,
                ROW_NUMBER() OVER (
                    PARTITION BY entity_id
                    ORDER BY datetime(updated_at) DESC, source_id DESC
                ) AS rn
            FROM source_manifest
            WHERE status='active'
              AND source_type='external_source_snapshot'
              AND json_extract(metadata_json, '$.source_kind')='public_analyst_signal'
        )
        WHERE rn=1
        ORDER BY datetime(updated_at) DESC, entity_id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    items = []
    for entity_id, title, source_rel_path, metadata_json, updated_at in rows:
        metadata = parse_metadata_json(metadata_json)
        meta_payload = load_json_rel_path(metadata.get("meta_rel_path"))
        if not meta_payload:
            continue
        items.append(
            enrich_snapshot(
                {
                "ts_code": entity_id,
                "name": meta_payload.get("company_name") or entity_id,
                "sector": None,
                "pool_types": [],
                "score": None,
                "source_kind": "public_analyst_signal",
                "provider": meta_payload.get("provider") or "marketscreener",
                "title": title,
                "source_rel_path": source_rel_path,
                "updated_at": updated_at,
                "published_at": meta_payload.get("published_at"),
                "snapshot_date": meta_payload.get("snapshot_date"),
                "mean_consensus": meta_payload.get("mean_consensus"),
                "analysts_count": meta_payload.get("analysts_count"),
                "last_close_price": meta_payload.get("last_close_price"),
                "last_close_currency": meta_payload.get("last_close_currency"),
                "last_close_raw": meta_payload.get("last_close_raw"),
                "average_target_price": meta_payload.get("average_target_price"),
                "average_target_currency": meta_payload.get("average_target_currency"),
                "average_target_raw": meta_payload.get("average_target_raw"),
                "spread_avg_target_pct": meta_payload.get("spread_avg_target_pct"),
                "high_target_price": meta_payload.get("high_target_price"),
                "high_target_currency": meta_payload.get("high_target_currency"),
                "high_target_raw": meta_payload.get("high_target_raw"),
                "spread_high_target_pct": meta_payload.get("spread_high_target_pct"),
                "low_target_price": meta_payload.get("low_target_price"),
                "low_target_currency": meta_payload.get("low_target_currency"),
                "low_target_raw": meta_payload.get("low_target_raw"),
                "spread_low_target_pct": meta_payload.get("spread_low_target_pct"),
                }
            )
        )
    return items


def load_public_analyst_signal_digest(conn, limit=7, focus_ts_codes=None, fallback_to_pool=True):
    requested_codes = [ts_code for ts_code in (focus_ts_codes or []) if ts_code]
    if requested_codes:
        focus_strategy = "explicit_ts_codes"
        focus_items = load_focus_equities(
            conn,
            limit=max(limit, len(requested_codes)),
            focus_ts_codes=requested_codes,
        )
    elif fallback_to_pool:
        focus_strategy = "top_pool"
        focus_items = load_focus_equities(conn, limit=limit)
    else:
        focus_strategy = "none"
        focus_items = []

    items = []
    for focus in focus_items[:limit]:
        snapshot = latest_public_analyst_signal_snapshot(conn, focus["ts_code"])
        if not snapshot:
            continue
        items.append(
            {
                "ts_code": focus["ts_code"],
                "name": focus["name"],
                "sector": focus["sector"],
                "pool_types": focus["pool_types"],
                "score": focus["score"],
                **snapshot,
            }
        )

    if not items and fallback_to_pool:
        items = latest_public_analyst_signal_items(conn, limit=limit)
        if items:
            focus_strategy = "latest_signal_snapshots"

    return {
        "focus_strategy": focus_strategy,
        "requested_focus_count": len(requested_codes),
        "focus_count": len(items),
        "focus_ts_codes": requested_codes[:limit],
        "items": items,
    }
