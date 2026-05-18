#!/usr/bin/env python3
"""Build a unified source manifest for research, reports, pool snapshots, and risk snapshots."""

import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import (
    dumps_json,
    ensure_source_manifest_table,
    extract_frontmatter,
    extract_title,
    markdown_timestamp,
    now_ts,
    normalized_source_path,
    normalize_tags,
    read_markdown,
    slugify,
)

DB_PATH = project_path("01_data", "db", "smr.db")
DAILY_REPORT_DIR = project_path("06_reports", "daily")
RISK_ALERT_DIR = project_path("05_risk", "alerts")
POOL_SNAPSHOT_DIR = project_path("03_stock_pool", "watchlist")
DISPATCH_BOARD_PATH = project_path("00_control", "dispatch_board.md")
MANIFEST_SNAPSHOT_PATH = project_path("11_smr_wiki", "raw", "manifests", "source_manifest_latest.md")
EXTERNAL_SOURCE_DIR = project_path("11_smr_wiki", "raw", "external")

RESEARCH_TYPE_MAP = {
    "industry": ("industry_research", "sector"),
    "stock": ("stock_research", "stock"),
    "recommendation": ("recommendation_card", "stock"),
}


def count_by_source_type(rows):
    counts = {}
    for row in rows:
        counts[row["source_type"]] = counts.get(row["source_type"], 0) + 1
    return counts


def build_research_rows(conn):
    rows = []
    result = conn.execute(
        """
        SELECT report_id, report_type, sector, title, ts_codes, created_at, file_path
        FROM research_index
        ORDER BY datetime(created_at) DESC
        """
    ).fetchall()

    for report_id, report_type, sector, title, ts_codes, created_at, file_path in result:
        source_type, entity_type = RESEARCH_TYPE_MAP.get(report_type, ("research_note", "research"))
        entity_id = sector if report_type == "industry" else (ts_codes or report_id)
        source_path, source_rel_path = normalized_source_path(file_path)
        if not source_path:
            continue
        rows.append(
            {
                "source_id": f"{source_type}__{report_id}",
                "source_type": source_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": title or report_id,
                "source_path": source_path,
                "source_rel_path": source_rel_path,
                "status": "active",
                "created_at": created_at or markdown_timestamp(source_path),
                "updated_at": markdown_timestamp(source_path) or created_at,
                "upstream_refs": [value.strip() for value in (ts_codes or "").split(",") if value.strip()],
                "tags": normalize_tags([source_type, entity_type, entity_id, sector, report_type]),
                "metadata_json": dumps_json(
                    {
                        "report_id": report_id,
                        "report_type": report_type,
                        "sector": sector,
                        "ts_codes": [value.strip() for value in (ts_codes or "").split(",") if value.strip()],
                    }
                ),
            }
        )
    return rows


def build_markdown_rows(directory, source_type, entity_type, entity_builder):
    rows = []
    if not directory.exists():
        return rows

    for path in sorted(directory.glob("*.md")):
        text = read_markdown(path)
        entity_id, upstream_refs, extra_tags = entity_builder(path, text)
        source_path, source_rel_path = normalized_source_path(path)
        rows.append(
            {
                "source_id": f"{source_type}__{path.stem}",
                "source_type": source_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": extract_title(text, fallback=path.stem),
                "source_path": source_path,
                "source_rel_path": source_rel_path,
                "status": "active",
                "created_at": markdown_timestamp(path),
                "updated_at": markdown_timestamp(path),
                "upstream_refs": upstream_refs,
                "tags": normalize_tags([source_type, entity_type, entity_id, *extra_tags]),
                "metadata_json": dumps_json({}),
            }
        )
    return rows


def daily_report_entity(path, _text):
    report_date = path.stem.split("_", 1)[0]
    return report_date, [report_date], [path.stem]


def risk_alert_entity(path, _text):
    report_date = path.stem.split("_", 1)[0]
    return report_date, [report_date], ["risk"]


def pool_snapshot_entity(path, _text):
    report_date = path.stem.split("_", 1)[0]
    return report_date, [report_date], ["dynamic_pool"]


def build_dispatch_row():
    text = read_markdown(DISPATCH_BOARD_PATH)
    source_path, source_rel_path = normalized_source_path(DISPATCH_BOARD_PATH)
    return {
        "source_id": "dispatch_snapshot__dispatch_board",
        "source_type": "dispatch_snapshot",
        "entity_type": "system",
        "entity_id": "dispatch_board",
        "title": extract_title(text, fallback="SMR 调度面板"),
        "source_path": source_path,
        "source_rel_path": source_rel_path,
        "status": "active",
        "created_at": markdown_timestamp(DISPATCH_BOARD_PATH),
        "updated_at": markdown_timestamp(DISPATCH_BOARD_PATH),
        "upstream_refs": ["dispatch_board"],
        "tags": normalize_tags(["dispatch_snapshot", "system", "dispatch_board"]),
        "metadata_json": dumps_json({}),
    }


def build_external_rows():
    rows = []
    if not EXTERNAL_SOURCE_DIR.exists():
        return rows

    for path in sorted(EXTERNAL_SOURCE_DIR.rglob("*.md")):
        text = read_markdown(path)
        metadata = extract_frontmatter(text)
        source_url = metadata.get("source_url")
        if not source_url:
            continue
        entity_type = metadata.get("entity_type") or "external_source"
        entity_id = metadata.get("entity_id") or path.stem
        source_kind = metadata.get("source_kind") or "external"
        title = metadata.get("title") or extract_title(text, fallback=path.stem)
        tags = [value.strip() for value in metadata.get("tags", "").split(",") if value.strip()]
        source_path, source_rel_path = normalized_source_path(path)
        provider = metadata.get("provider") or source_kind
        stable_key = metadata.get("announcement_id") or metadata.get("source_url") or path.stem
        rows.append(
            {
                "source_id": f"external_source__{slugify(provider)}__{slugify(stable_key)[:120]}",
                "source_type": "external_source_snapshot",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": title,
                "source_path": source_path,
                "source_rel_path": source_rel_path,
                "status": "active",
                "created_at": metadata.get("fetched_at") or markdown_timestamp(path),
                "updated_at": markdown_timestamp(path) or metadata.get("fetched_at"),
                "upstream_refs": [source_url, metadata.get("source_domain") or ""],
                "tags": normalize_tags(["external_source_snapshot", source_kind, entity_type, entity_id, *tags]),
                "metadata_json": dumps_json(
                    {
                        "source_url": source_url,
                        "source_kind": source_kind,
                        "source_domain": metadata.get("source_domain"),
                        "content_type": metadata.get("content_type"),
                        "fetched_at": metadata.get("fetched_at"),
                        "raw_rel_path": metadata.get("raw_rel_path"),
                        "meta_rel_path": metadata.get("meta_rel_path"),
                    }
                ),
            }
        )
    return rows


def upsert_rows(conn, rows):
    for row in rows:
        conn.execute(
            """
            INSERT INTO source_manifest (
                source_id,
                source_type,
                entity_type,
                entity_id,
                title,
                source_path,
                source_rel_path,
                status,
                created_at,
                updated_at,
                upstream_refs,
                tags,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                source_type=excluded.source_type,
                entity_type=excluded.entity_type,
                entity_id=excluded.entity_id,
                title=excluded.title,
                source_path=excluded.source_path,
                source_rel_path=excluded.source_rel_path,
                status=excluded.status,
                updated_at=excluded.updated_at,
                upstream_refs=excluded.upstream_refs,
                tags=excluded.tags,
                metadata_json=excluded.metadata_json
            """,
            (
                row["source_id"],
                row["source_type"],
                row["entity_type"],
                row["entity_id"],
                row["title"],
                row["source_path"],
                row["source_rel_path"],
                row["status"],
                row["created_at"],
                row["updated_at"],
                dumps_json(row["upstream_refs"]),
                dumps_json(row["tags"]),
                row["metadata_json"],
            ),
            )


def dedupe_rows(rows):
    unique_rows = {}
    for row in rows:
        existing = unique_rows.get(row["source_id"])
        if existing is None:
            unique_rows[row["source_id"]] = row
            continue
        existing_sort_key = (
            existing.get("updated_at") or existing.get("created_at") or "",
            existing.get("source_rel_path") or "",
        )
        current_sort_key = (
            row.get("updated_at") or row.get("created_at") or "",
            row.get("source_rel_path") or "",
        )
        if current_sort_key >= existing_sort_key:
            unique_rows[row["source_id"]] = row
    return unique_rows


def write_snapshot(rows):
    def escape_cell(value):
        return str(value).replace("|", "\\|")

    counts = count_by_source_type(rows)
    MANIFEST_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# SMR Wiki Source Manifest Snapshot",
        "",
        f"- generated_at: {now_ts()}",
        f"- total_sources: {len(rows)}",
        "",
        "## Counts By Type",
        "",
    ]
    for source_type in sorted(counts):
        lines.append(f"- `{source_type}`: {counts[source_type]}")

    lines.extend(
        [
            "",
            "## Sources",
            "",
            "| source_id | source_type | entity_type | entity_id | title | path |",
            "|-----------|-------------|-------------|-----------|-------|------|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {escape_cell(row['source_id'])} | {escape_cell(row['source_type'])} | {escape_cell(row['entity_type'])} | "
            f"{escape_cell(row['entity_id'])} | {escape_cell(row['title'])} | {escape_cell(row['source_rel_path'])} |"
        )

    MANIFEST_SNAPSHOT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_source_manifest_table(conn)

    rows = []
    rows.extend(build_research_rows(conn))
    rows.extend(build_markdown_rows(DAILY_REPORT_DIR, "daily_report", "market_day", daily_report_entity))
    rows.extend(build_markdown_rows(RISK_ALERT_DIR, "risk_alert_snapshot", "risk_cycle", risk_alert_entity))
    rows.extend(build_markdown_rows(POOL_SNAPSHOT_DIR, "pool_snapshot", "market_day", pool_snapshot_entity))
    rows.extend(build_external_rows())
    rows.append(build_dispatch_row())

    unique_rows = dedupe_rows(rows)
    ordered_rows = sorted(unique_rows.values(), key=lambda row: (row["source_type"], row["source_id"]))
    counts_by_type = count_by_source_type(ordered_rows)

    # Rebuild current source_manifest from scratch so stale source_ids do not linger.
    conn.execute("DELETE FROM source_manifest")
    upsert_rows(conn, ordered_rows)
    write_snapshot(ordered_rows)
    register_snapshot(
        conn,
        entity_type="source_manifest",
        entity_id="source_manifest_latest",
        status="updated",
        source="build_source_manifest.py",
        relationships={
            "snapshot_rel_path": relative_to_project(MANIFEST_SNAPSHOT_PATH),
        },
        payload={
            "source_count": len(ordered_rows),
            "counts_by_type": counts_by_type,
            "source_ids_sample": [row["source_id"] for row in ordered_rows[:10]],
            "generated_at": now_ts(),
        },
    )
    conn.commit()
    conn.close()
    log_run(
        "build_source_manifest.py",
        "success",
        "source manifest built",
        {
            "source_count": len(ordered_rows),
            "snapshot_path": str(MANIFEST_SNAPSHOT_PATH),
            "counts_by_type": counts_by_type,
        },
    )
    print(f"Source manifest updated: {len(ordered_rows)} sources")
    print(f"Snapshot: {MANIFEST_SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
