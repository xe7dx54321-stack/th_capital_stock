#!/usr/bin/env python3
"""Shared helpers for loading latest external research digests into downstream payloads."""

import json

from smr_paths import project_path
from smr_universe import combined_name_map, relation_exists
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


def load_focus_equities(conn, limit=5, focus_ts_codes=None):
    names = combined_name_map(conn)
    requested_codes = []
    seen = set()
    for ts_code in focus_ts_codes or []:
        if not ts_code or ts_code in seen:
            continue
        requested_codes.append(ts_code)
        seen.add(ts_code)

    if not relation_exists(conn, "stock_pool_current"):
        return [
            {
                "ts_code": ts_code,
                "sector": None,
                "score": None,
                "pool_types": [],
                "name": names.get(ts_code, ts_code),
            }
            for ts_code in requested_codes[:limit]
        ]

    if requested_codes:
        placeholders = ",".join("?" for _ in requested_codes)
        rows = conn.execute(
            f"""
            WITH ranked AS (
                SELECT
                    ts_code,
                    MAX(sector) AS sector,
                    MAX(score) AS max_score,
                    GROUP_CONCAT(DISTINCT pool_type) AS pool_types
                FROM stock_pool_current
                WHERE pool_type IN ('recommended', 'candidate', 'watchlist')
                  AND ts_code IN ({placeholders})
                GROUP BY ts_code
            )
            SELECT ts_code, sector, max_score, pool_types
            FROM ranked
            """,
            requested_codes,
        ).fetchall()
        row_map = {
            ts_code: {
                "sector": sector,
                "score": max_score,
                "pool_types": sorted([item for item in (pool_types or "").split(",") if item]),
            }
            for ts_code, sector, max_score, pool_types in rows
        }
        return [
            {
                "ts_code": ts_code,
                "sector": row_map.get(ts_code, {}).get("sector"),
                "score": row_map.get(ts_code, {}).get("score"),
                "pool_types": row_map.get(ts_code, {}).get("pool_types", []),
                "name": names.get(ts_code, ts_code),
            }
            for ts_code in requested_codes[:limit]
        ]

    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT
                ts_code,
                MAX(sector) AS sector,
                MAX(score) AS max_score,
                MIN(
                    CASE pool_type
                        WHEN 'recommended' THEN 0
                        WHEN 'candidate' THEN 1
                        WHEN 'watchlist' THEN 2
                        ELSE 9
                    END
                ) AS pool_rank,
                GROUP_CONCAT(DISTINCT pool_type) AS pool_types
            FROM stock_pool_current
            WHERE pool_type IN ('recommended', 'candidate', 'watchlist')
            GROUP BY ts_code
        )
        SELECT ts_code, sector, max_score, pool_types
        FROM ranked
        ORDER BY pool_rank ASC, max_score DESC, ts_code ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "ts_code": ts_code,
            "sector": sector,
            "score": max_score,
            "pool_types": sorted([item for item in (pool_types or "").split(",") if item]),
            "name": names.get(ts_code, ts_code),
        }
        for ts_code, sector, max_score, pool_types in rows
    ]


def latest_external_research_snapshot(conn, ts_code):
    snapshots = external_research_snapshots(conn, ts_code, limit=4)
    return snapshots[0] if snapshots else None


def normalize_external_research_payload(title, source_rel_path, metadata, raw_payload, updated_at):
    source_kind = metadata.get("source_kind")
    raw_rel_path = metadata.get("raw_rel_path")
    raw_name = str(raw_rel_path or "").rsplit("/", 1)[-1]
    report_key = raw_name.split("__research_", 1)[0] if "__research_" in raw_name else raw_name or source_rel_path
    if source_kind == "research_table_structured":
        normalized = raw_payload.get("forecast_table", {}).get("normalized_metrics", {})
        rating = raw_payload.get("rating", {})
        document = raw_payload.get("document", {})
        return {
            "report_key": report_key,
            "source_kind": source_kind,
            "title": title,
            "source_rel_path": source_rel_path,
            "updated_at": updated_at,
            "published_at": document.get("published_at"),
            "org_name": document.get("org_name"),
            "rating_name": document.get("rating_name"),
            "target_price_yuan": rating.get("target_price_yuan"),
            "revenue_billion": normalized.get("revenue_billion", {}),
            "net_profit_billion": normalized.get("net_profit_billion", {}),
            "eps_yuan": normalized.get("eps_yuan", {}),
            "pe_multiple": normalized.get("pe_multiple", {}),
            "roe_percent": normalized.get("roe_percent", {}),
        }

    if source_kind == "research_structured":
        metrics = raw_payload.get("forecast_metrics", {})
        document = raw_payload.get("document", {})
        return {
            "report_key": report_key,
            "source_kind": source_kind,
            "title": title,
            "source_rel_path": source_rel_path,
            "updated_at": updated_at,
            "published_at": document.get("published_at"),
            "org_name": document.get("org_name"),
            "rating_name": document.get("rating_name"),
            "target_price_yuan": metrics.get("target_price_yuan"),
            "revenue_billion": metrics.get("revenue_billion", {}),
            "net_profit_billion": metrics.get("net_profit_billion", {}),
            "eps_yuan": metrics.get("eps_yuan", {}),
            "pe_multiple": metrics.get("pe_multiple", {}),
            "roe_percent": {},
        }

    return None


def external_research_snapshots(conn, ts_code, limit=8):
    ensure_source_manifest_table(conn)
    rows = conn.execute(
        """
        SELECT title, source_rel_path, metadata_json, updated_at
        FROM source_manifest
        WHERE status='active'
          AND source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind') IN ('research_table_structured', 'research_structured')
        ORDER BY
            CASE json_extract(metadata_json, '$.source_kind')
                WHEN 'research_table_structured' THEN 0
                WHEN 'research_structured' THEN 1
                ELSE 9
            END ASC,
            datetime(updated_at) DESC,
            source_id DESC
        LIMIT ?
        """,
        (ts_code, max(limit * 3, limit)),
    ).fetchall()

    snapshots = []
    seen = set()
    for title, source_rel_path, metadata_json, updated_at in rows:
        metadata = parse_metadata_json(metadata_json)
        raw_payload = load_json_rel_path(metadata.get("raw_rel_path"))
        if not raw_payload:
            continue
        snapshot = normalize_external_research_payload(title, source_rel_path, metadata, raw_payload, updated_at)
        if not snapshot:
            continue
        dedupe_key = (
            snapshot.get("report_key"),
            snapshot.get("published_at"),
            snapshot.get("org_name"),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        snapshots.append(snapshot)
        if len(snapshots) >= limit:
            break
    return snapshots


def load_external_research_digest(conn, limit=5, focus_ts_codes=None, fallback_to_pool=True):
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
        snapshot = latest_external_research_snapshot(conn, focus["ts_code"])
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

    return {
        "focus_strategy": focus_strategy,
        "requested_focus_count": len(requested_codes),
        "focus_count": len(items),
        "focus_ts_codes": requested_codes[:limit],
        "items": items,
    }
