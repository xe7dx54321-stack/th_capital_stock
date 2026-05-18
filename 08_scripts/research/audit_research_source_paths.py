#!/usr/bin/env python3
"""Audit research_index file paths for current-machine reproducibility."""

import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
REPORT_PATH = project_path("02_research", "summary", "research_source_audit_latest.md")


def classify_path(raw_path):
    normalized = normalize_project_path(raw_path)
    normalized_str = str(normalized) if normalized else ""
    path_obj = Path(normalized_str) if normalized_str else None
    if not raw_path:
        return {
            "status": "missing_path",
            "raw_path": raw_path,
            "normalized_path": None,
            "rel_path": None,
            "exists": False,
        }
    if normalized_str and str(raw_path) != normalized_str:
        return {
            "status": "legacy_path_mapped_exists" if path_obj and path_obj.exists() else "legacy_path_missing",
            "raw_path": raw_path,
            "normalized_path": normalized_str,
            "rel_path": relative_to_project(path_obj) if path_obj and path_obj.exists() else relative_to_project(normalized) if normalized else None,
            "exists": bool(path_obj and path_obj.exists()),
        }
    return {
        "status": "current_path_exists" if path_obj and path_obj.exists() else "current_path_missing",
        "raw_path": raw_path,
        "normalized_path": normalized_str,
        "rel_path": relative_to_project(path_obj) if path_obj and path_obj.exists() else relative_to_project(normalized) if normalized else None,
        "exists": bool(path_obj and path_obj.exists()),
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT report_id, report_type, sector, title, ts_codes, created_at, file_path
        FROM research_index
        ORDER BY datetime(created_at) DESC, report_id DESC
        """
    ).fetchall()

    classified = []
    counts = Counter()
    for report_id, report_type, sector, title, ts_codes, created_at, file_path in rows:
        path_status = classify_path(file_path)
        counts[path_status["status"]] += 1
        classified.append(
            {
                "report_id": report_id,
                "report_type": report_type,
                "sector": sector,
                "title": title,
                "ts_codes": ts_codes,
                "created_at": created_at,
                **path_status,
            }
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Research Source Audit",
        "",
        f"- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- total_reports: {len(classified)}",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(
        [
            "",
            "## Entries",
            "",
            "| report_id | type | status | title | raw_path | normalized |",
            "|-----------|------|--------|-------|----------|------------|",
        ]
    )
    for item in classified:
        lines.append(
            "| {report_id} | {report_type} | {status} | {title} | {raw_path} | {normalized} |".format(
                report_id=str(item["report_id"]).replace("|", "\\|"),
                report_type=str(item["report_type"]).replace("|", "\\|"),
                status=item["status"],
                title=str(item["title"] or "").replace("|", "\\|"),
                raw_path=str(item["raw_path"] or "").replace("|", "\\|"),
                normalized=str(item["rel_path"] or item["normalized_path"] or "").replace("|", "\\|"),
            )
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    register_snapshot(
        conn,
        entity_type="research_source_audit",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="audited" if classified else "empty",
        source="audit_research_source_paths.py",
        relationships={"report_rel_path": relative_to_project(REPORT_PATH)},
        payload={
            "total_reports": len(classified),
            "counts_by_status": dict(counts),
            "sample_reports": [item["report_id"] for item in classified[:10]],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "audit_research_source_paths.py",
        "success",
        "research source paths audited",
        {
            "total_reports": len(classified),
            "counts_by_status": dict(counts),
            "report_path": str(REPORT_PATH),
        },
    )
    print(f"Research source audit written: {REPORT_PATH}")
    for key in sorted(counts):
        print(f"- {key}: {counts[key]}")


if __name__ == "__main__":
    main()
