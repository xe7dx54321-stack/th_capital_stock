#!/usr/bin/env python3
"""Register the current daily reporting surface into task registry."""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, relative_to_project
from smr_agents import ensure_auto_handoff
from smr_external_research import load_external_research_digest
from smr_flow_event_digest import latest_capital_flow_fact_sheet
from smr_official_materials import load_official_material_digest
from smr_public_analyst_digest import load_public_analyst_signal_digest
from smr_public_transcripts import load_public_transcript_digest
from smr_reporting_priority import build_high_value_reporting_digest
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import extract_first_paragraph, extract_title, markdown_timestamp, read_markdown
from build_daily_report_candidate import build_daily_report_candidate_for_snapshot

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
DAILY_REPORT_DIR = env_or_project_path("SMR_DAILY_REPORT_DIR", "06_reports", "daily")
DISPATCH_BOARD_PATH = env_or_project_path("SMR_DISPATCH_BOARD_PATH", "00_control", "dispatch_board.md")


def latest_daily_report():
    if not DAILY_REPORT_DIR.exists():
        return None
    reports = [path for path in DAILY_REPORT_DIR.glob("*.md") if path.is_file()]
    if not reports:
        return None
    return sorted(reports, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[0]


def load_pool_counts(conn):
    rows = conn.execute(
        """
        SELECT pool_type, count(*)
        FROM stock_pool_current
        WHERE pool_type IN ('watchlist', 'candidate', 'recommended')
        GROUP BY pool_type
        ORDER BY pool_type
        """
    ).fetchall()
    return {pool_type: count for pool_type, count in rows}


def latest_report_date(report_path):
    if report_path is None:
        return datetime.now().strftime("%Y-%m-%d")
    return report_path.stem.split("_", 1)[0]


def parse_date_value(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except ValueError:
            continue
    return None


def latest_surface_date(conn):
    entity_types = (
        "stock_objective_monitor_snapshot",
        "strategy_watch_batch",
        "rotation_candidate_snapshot",
        "rotation_execution_plan_snapshot",
        "portfolio_action_memo_snapshot",
        "risk_monitor_snapshot",
        "market_event_snapshot",
    )
    best_dt = None
    for entity_type in entity_types:
        row = conn.execute(
            """
            SELECT entity_id
            FROM task_registry_entity_latest
            WHERE entity_type=?
            ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
            LIMIT 1
            """,
            (entity_type,),
        ).fetchone()
        if not row:
            continue
        parsed = parse_date_value(row[0])
        if parsed and (best_dt is None or parsed > best_dt):
            best_dt = parsed
    return best_dt.strftime("%Y-%m-%d") if best_dt else None


def latest_objective_monitor_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='stock_objective_monitor_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "monitor_rel_path": relationships.get("monitor_rel_path") or payload.get("monitor_rel_path"),
        "focus_strategy": payload.get("focus_strategy"),
        "focus_count": payload.get("focus_count", 0),
        "objective_view_counts": payload.get("objective_view_counts") or {},
        "items": payload.get("items") or [],
    }


def latest_strategy_watch_batch(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='strategy_watch_batch'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "summary_rel_path": relationships.get("summary_rel_path") or payload.get("summary_rel_path"),
        "objective_monitor_rel_path": relationships.get("objective_monitor_rel_path"),
        "focus_strategy": payload.get("focus_strategy"),
        "item_count": payload.get("item_count", 0),
        "priority_counts": payload.get("priority_counts") or {},
        "top_focus_items": payload.get("top_focus_items") or [],
        "items": payload.get("items") or [],
    }


def latest_rotation_candidate_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='rotation_candidate_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "summary_rel_path": relationships.get("summary_rel_path") or payload.get("summary_rel_path"),
        "holdings_reference_count": payload.get("holdings_reference_count", 0),
        "opportunity_count": payload.get("opportunity_count", 0),
        "rotation_pair_count": payload.get("rotation_pair_count", 0),
        "top_add_candidates": payload.get("top_add_candidates") or [],
        "top_reduce_candidates": payload.get("top_reduce_candidates") or [],
        "rotation_pairs": payload.get("rotation_pairs") or [],
    }


def latest_rotation_execution_plan_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='rotation_execution_plan_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "summary_rel_path": relationships.get("summary_rel_path") or payload.get("summary_rel_path"),
        "rotation_snapshot_rel_path": relationships.get("rotation_snapshot_rel_path"),
        "plan_mode": payload.get("plan_mode"),
        "holding_count": payload.get("holding_count", 0),
        "slot_capital": payload.get("slot_capital"),
        "slot_pct": payload.get("slot_pct"),
        "total_exposure_pct": payload.get("total_exposure_pct"),
        "plan_count": payload.get("plan_count", 0),
        "status_counts": payload.get("status_counts") or {},
        "plans": payload.get("plans") or [],
    }


def latest_portfolio_action_memo_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='portfolio_action_memo_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "summary_rel_path": relationships.get("summary_rel_path") or payload.get("summary_rel_path"),
        "objective_monitor_rel_path": relationships.get("objective_monitor_rel_path"),
        "strategy_watch_rel_path": relationships.get("strategy_watch_rel_path"),
        "rotation_snapshot_rel_path": relationships.get("rotation_snapshot_rel_path"),
        "execution_plan_rel_path": relationships.get("execution_plan_rel_path"),
        "action_mode": payload.get("action_mode"),
        "action_count": payload.get("action_count", 0),
        "priority_counts": payload.get("priority_counts") or {},
        "action_type_counts": payload.get("action_type_counts") or {},
        "primary_call": payload.get("primary_call") or [],
        "actions": payload.get("actions") or [],
    }


def latest_risk_monitor_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='risk_monitor_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "alert_count": payload.get("alert_count", 0),
        "counts_by_severity": payload.get("counts_by_severity") or {},
        "counts_by_type": payload.get("counts_by_type") or {},
        "open_position_count": payload.get("open_position_count", 0),
        "unacknowledged_alert_count": payload.get("unacknowledged_alert_count", 0),
        "reference_observations": payload.get("reference_observations") or [],
        "alert_file_rel_path": relationships.get("alert_file_rel_path") or payload.get("alert_file_rel_path"),
        "observation_file_rel_path": relationships.get("observation_file_rel_path")
        or payload.get("observation_file_rel_path"),
    }


def latest_market_flow_anomaly_snapshot(conn):
    row = conn.execute(
        """
        SELECT relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type='market_flow_anomaly_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    relationships = json.loads(row[0] or "{}")
    payload = json.loads(row[1] or "{}")
    return {
        "created_at": row[2],
        "batch_date": payload.get("batch_date"),
        "overview_lines": payload.get("overview_lines") or [],
        "coverage_summary": payload.get("coverage_summary") or {},
        "markets": payload.get("markets") or {},
        "summary_rel_path": relationships.get("summary_rel_path") or payload.get("summary_rel_path"),
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    latest_report_path = latest_daily_report()
    latest_report_text = read_markdown(latest_report_path) if latest_report_path else ""
    dispatch_text = read_markdown(DISPATCH_BOARD_PATH)
    report_anchor_date = latest_report_date(latest_report_path)
    surface_date = latest_surface_date(conn) or report_anchor_date

    payload = {
        "report_surface_date": surface_date,
        "latest_report_anchor_date": report_anchor_date,
        "latest_report_is_aligned": report_anchor_date == surface_date,
        "report_count": len(list(DAILY_REPORT_DIR.glob("*.md"))) if DAILY_REPORT_DIR.exists() else 0,
        "latest_report_rel_path": relative_to_project(latest_report_path) if latest_report_path else None,
        "latest_report_title": extract_title(latest_report_text, fallback="") if latest_report_text else None,
        "latest_report_summary": extract_first_paragraph(latest_report_text) if latest_report_text else None,
        "latest_report_updated_at": markdown_timestamp(latest_report_path) if latest_report_path else None,
        "dispatch_board_rel_path": relative_to_project(DISPATCH_BOARD_PATH),
        "dispatch_board_title": extract_title(dispatch_text, fallback="SMR 调度面板"),
        "dispatch_board_updated_at": markdown_timestamp(DISPATCH_BOARD_PATH),
        "pool_counts": load_pool_counts(conn),
        "open_position_count": conn.execute("SELECT COUNT(*) FROM position WHERE status='open'").fetchone()[0],
        "unacknowledged_alert_count": conn.execute(
            "SELECT COUNT(*) FROM risk_alert WHERE acknowledged=0"
        ).fetchone()[0],
        "external_research_digest": load_external_research_digest(conn),
        "official_material_digest": load_official_material_digest(conn),
        "public_transcript_digest": load_public_transcript_digest(conn),
        "public_analyst_signal_digest": load_public_analyst_signal_digest(conn),
        "capital_flow_fact_sheet": latest_capital_flow_fact_sheet(conn),
        "market_flow_anomaly_snapshot": latest_market_flow_anomaly_snapshot(conn),
        "objective_monitor_snapshot": latest_objective_monitor_snapshot(conn),
        "strategy_watch_batch": latest_strategy_watch_batch(conn),
        "rotation_candidate_snapshot": latest_rotation_candidate_snapshot(conn),
        "rotation_execution_plan_snapshot": latest_rotation_execution_plan_snapshot(conn),
        "portfolio_action_memo_snapshot": latest_portfolio_action_memo_snapshot(conn),
        "risk_monitor_snapshot": latest_risk_monitor_snapshot(conn),
    }
    payload["high_value_reporting_digest"] = build_high_value_reporting_digest(
        payload["external_research_digest"],
        payload["official_material_digest"],
        payload["public_transcript_digest"],
        payload["public_analyst_signal_digest"],
    )

    entity_id = surface_date
    registry_entry = register_snapshot(
        conn,
        entity_type="daily_reporting_snapshot",
        entity_id=entity_id,
        status="recorded" if latest_report_path and report_anchor_date == surface_date else "candidate_pending",
        source="snapshot_daily_reporting.py",
        relationships={
            "latest_report_rel_path": payload["latest_report_rel_path"],
            "dispatch_board_rel_path": payload["dispatch_board_rel_path"],
        },
        payload=payload,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="日报快照已更新，自动转交 Hermes-like 日报代理补充解释。",
        created_by="snapshot_daily_reporting.py",
    )
    candidate_result = build_daily_report_candidate_for_snapshot(
        conn,
        registry_entry,
        created_at=registry_entry["created_at"],
    )
    conn.commit()
    conn.close()

    log_run(
        "snapshot_daily_reporting.py",
        "success",
        "daily reporting surface snapshotted",
        {
            "entity_id": entity_id,
            "latest_report_rel_path": payload["latest_report_rel_path"],
            "dispatch_board_rel_path": payload["dispatch_board_rel_path"],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
            "candidate_rel_path": relative_to_project(candidate_result["output_path"]),
            "candidate_handoff_id": candidate_result["handoff_result"]["handoff"]["handoff_id"]
            if candidate_result["handoff_result"]["handoff"]
            else None,
        },
    )
    print(f"Daily reporting snapshot registered: {entity_id}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")
    print(f"Daily report candidate: {candidate_result['output_path']}")
    if candidate_result["handoff_result"]["handoff"]:
        print(
            f"Candidate handoff {candidate_result['handoff_result']['reason']}: "
            f"{candidate_result['handoff_result']['handoff']['handoff_id']} -> "
            f"{candidate_result['handoff_result']['handoff']['to_profile_id']}"
        )
    else:
        print(f"Candidate handoff skipped: {candidate_result['handoff_result']['reason']}")


if __name__ == "__main__":
    main()
