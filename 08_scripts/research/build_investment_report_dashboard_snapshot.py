#!/usr/bin/env python3
"""Parse report-writer output into dashboard-ready investment report snapshots."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_bear_case import build_bear_case
from smr_claim_graph import build_claim_evidence_graph, claim_evidence_map, claim_graph_summary
from smr_consensus_proxy import build_consensus_revision_proxy
from smr_data_health import check_freshness_gate, gate_to_dict
from smr_decision import determine_recommendation_status, parse_primary_ticker, record_agent_run, upsert_decision_ledger
from smr_investment_reports import load_text_rel_path, parse_report_dashboard_payload
from smr_registry import register_snapshot
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion, promotion_to_dict
from smr_research_quality import check_report_evidence, lint_report, quality_to_dict
from smr_runlog import log_run
from smr_source_registry import source_registry_snapshot
from smr_valuation import build_valuation_snapshot

SCRIPT_NAME = "build_investment_report_dashboard_snapshot.py"


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def action_id_from_entity(entity_id: str | None) -> str | None:
    text = str(entity_id or "")
    if "__" not in text:
        return None
    return text.split("__", 1)[1]


def latest_report_entries(conn: sqlite3.Connection, action_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE entity_type='investment_report_snapshot'
          AND source != ?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (SCRIPT_NAME, max(limit * 4, limit)),
    ).fetchall()
    entries = []
    seen = set()
    for row in rows:
        payload = load_json(row["payload_json"], {})
        entity_id = row["entity_id"]
        candidate_action_id = payload.get("action_id") or action_id_from_entity(entity_id)
        if action_id and candidate_action_id != action_id:
            continue
        if entity_id in seen:
            continue
        seen.add(entity_id)
        entries.append(
            {
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": entity_id,
                "status": row["status"],
                "source": row["source"],
                "relationships": load_json(row["relationships_json"], {}),
                "payload": payload,
                "snapshot_index": row["snapshot_index"],
                "created_at": row["created_at"],
            }
        )
        if len(entries) >= limit:
            break
    return entries


def parse_entry(conn: sqlite3.Connection, entry: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    payload = entry.get("payload") or {}
    relationships = entry.get("relationships") or {}
    report_rel_path = payload.get("report_md_rel_path") or payload.get("model_response_text_rel_path")
    evidence_rel_path = (
        payload.get("evidence_pack_md_rel_path")
        or payload.get("source_pack_md_rel_path")
        or relationships.get("evidence_pack_md_rel_path")
    )
    parsed = parse_report_dashboard_payload(report_rel_path, evidence_rel_path)
    report_text = load_text_rel_path(report_rel_path)
    evidence_text = load_text_rel_path(evidence_rel_path)
    dashboard_summary = parsed.get("dashboard_summary") or {}
    freshness_gate = check_freshness_gate(
        conn,
        module_name="report_generation",
        required_data_types=["daily_bar", "filings", "fundamentals", "consensus_revision"],
        allow_degraded=True,
    )
    claim_summary = build_claim_evidence_graph(
        conn,
        report_id=entry["entity_id"],
        recommendation_id=entry["id"],
        report_text=report_text,
        evidence_pack_text=evidence_text,
        dashboard_summary=dashboard_summary,
    )
    claim_map = claim_evidence_map(conn, entry["entity_id"])
    evidence_ids = []
    for claim in claim_map:
        for evidence in claim.get("evidence") or []:
            evidence_id = evidence.get("evidence_id")
            if evidence_id and evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
    ticker, _market = parse_primary_ticker(dashboard_summary.get("action_detail") or "")
    entity_ticker, entity_market = parse_primary_ticker(entry.get("entity_id") or "")
    if not ticker or ("." in str(entity_ticker or "") and "." not in str(ticker or "")):
        ticker, _market = entity_ticker, entity_market
    valuation_snapshot = build_valuation_snapshot(conn, ticker, freshness_gate.data_health_snapshot) if ticker else {}
    consensus_proxy = build_consensus_revision_proxy(
        conn,
        f"{dashboard_summary.get('confidence_rationale') or ''}\n{report_text or ''}",
        evidence_ids=evidence_ids[:8],
        ticker=ticker,
    ) if ticker else {}
    bear_case_result = build_bear_case(
        conn,
        report_id=entry["entity_id"],
        recommendation_id=entry["id"],
        dashboard_summary=dashboard_summary,
        valuation_snapshot=valuation_snapshot,
        missing_data=source_registry_snapshot().get("disabled_or_planned") or [],
        evidence_ids=evidence_ids,
    )
    claim_summary = claim_graph_summary(conn, entry["entity_id"])
    dashboard_summary = {
        **dashboard_summary,
        "valuation_snapshot": valuation_snapshot,
        "bear_case_summary": "; ".join(item.get("claim_text", "") for item in (bear_case_result.get("bear_case_claims") or [])[:2]),
        "bear_case_result": bear_case_result,
    }
    evidence_check = check_report_evidence(
        report_text,
        dashboard_summary=dashboard_summary,
        evidence_pack_text=evidence_text,
    )
    evidence_check_dict = quality_to_dict(evidence_check)
    evidence_check_dict["claim_evidence_summary"] = claim_summary
    if claim_summary.get("unsupported_core_claims"):
        evidence_check_dict["passed"] = False
        evidence_check_dict["severity"] = "block"
        evidence_check_dict["recommendation_allowed"] = False
        evidence_check_dict.setdefault("reasons", []).append("claim-level evidence graph 存在 unsupported core claim。")
    src_snapshot = source_registry_snapshot()
    lint_result = lint_report(
        report_text,
        dashboard_summary=dashboard_summary,
        freshness_gate_result=freshness_gate,
        evidence_check_result=evidence_check_dict,
        source_snapshot=src_snapshot,
    )
    recommendation_status, status_reasons = determine_recommendation_status(
        dashboard_summary,
        freshness_gate,
        evidence_check_dict,
        lint_result,
    )
    promotion_result = evaluate_promotion(
        conn,
        report_id=entry["entity_id"],
        recommendation_id=entry["id"],
        from_status=recommendation_status,
        dashboard_summary={
            **dashboard_summary,
            "ticker": ticker,
            "suggested_position_pct": dashboard_summary.get("suggested_position_pct"),
            "max_position_pct": dashboard_summary.get("max_position_pct"),
        },
        data_health_snapshot=freshness_gate.data_health_snapshot,
        evidence_check_snapshot=evidence_check_dict,
        claim_graph_snapshot=claim_summary,
        valuation_snapshot=valuation_snapshot,
        consensus_proxy=consensus_proxy,
        bear_case=bear_case_result,
        risk_snapshot={},
        lint_result=quality_to_dict(lint_result),
        write_ledger=False,
    )
    candidate_result = build_recommendation_candidate(
        conn,
        recommendation_id=entry["id"],
        ticker=ticker,
        report=dashboard_summary,
        claim_graph=claim_summary,
        evidence_check=evidence_check_dict,
        valuation_snapshot=valuation_snapshot,
        consensus_proxy=consensus_proxy,
        bear_case=bear_case_result,
        risk_snapshot={},
        market_signal={},
        promotion_result=promotion_result,
        write_ledger=False,
    )
    if promotion_result.allowed:
        recommendation_status = candidate_result.get("status") or "pending_human_review"
        status_reasons = candidate_result.get("reasons") or promotion_result.reasons
    else:
        recommendation_status = promotion_result.to_status
        status_reasons = promotion_result.reasons + [f"missing: {item}" for item in promotion_result.missing_requirements]
    enhanced_payload = {
        **payload,
        **parsed,
        "dashboard_summary": dashboard_summary,
        "report_md_rel_path": report_rel_path,
        "evidence_pack_md_rel_path": evidence_rel_path,
        "dashboard_parse_source_entry_id": entry.get("id"),
        "dashboard_parse_status": "parsed",
        "data_health_snapshot": freshness_gate.data_health_snapshot,
        "freshness_gate_result": gate_to_dict(freshness_gate),
        "source_registry_snapshot": src_snapshot,
        "missing_data": src_snapshot.get("disabled_or_planned") or [],
        "claim_evidence_summary": claim_summary,
        "claim_evidence_map": claim_map,
        "consensus_revision_proxy": consensus_proxy,
        "valuation_snapshot": valuation_snapshot,
        "bear_case_result": bear_case_result,
        "evidence_check_result": evidence_check_dict,
        "lint_result": quality_to_dict(lint_result),
        "promotion_result": promotion_to_dict(promotion_result),
        "recommendation_candidate": candidate_result,
        "recommendation_status": recommendation_status,
        "recommendation_state_reasons": status_reasons,
    }
    enhanced_relationships = {
        **relationships,
        "dashboard_parse_source_entry_id": entry.get("id"),
        "report_md_rel_path": report_rel_path,
        "evidence_pack_md_rel_path": evidence_rel_path,
    }
    if dry_run:
        return {
            "entity_id": entry["entity_id"],
            "report_rel_path": report_rel_path,
            "dashboard_summary_quality": parsed.get("dashboard_summary_quality"),
            "source_discipline_audit": parsed.get("source_discipline_audit"),
            "freshness_gate_status": freshness_gate.status,
            "evidence_check_severity": evidence_check_dict.get("severity"),
            "lint_max_severity": lint_result.max_severity,
            "recommendation_status": recommendation_status,
            "recommendation_state_reasons": status_reasons,
        }
    new_entry = register_snapshot(
        conn,
        entity_type="investment_report_snapshot",
        entity_id=entry["entity_id"],
        status=recommendation_status,
        source=SCRIPT_NAME,
        relationships=enhanced_relationships,
        payload=enhanced_payload,
    )
    upsert_decision_ledger(
        conn,
        recommendation_id=entry["id"],
        status=recommendation_status,
        dashboard_summary={
            **dashboard_summary,
            "action": candidate_result.get("action") or dashboard_summary.get("action"),
            "suggested_position_pct": candidate_result.get("suggested_position_pct"),
            "max_position_pct": candidate_result.get("max_position_pct"),
            "kill_triggers": candidate_result.get("kill_conditions") or dashboard_summary.get("kill_triggers") or [],
        },
        data_health_snapshot=freshness_gate.data_health_snapshot,
        evidence_check_snapshot=evidence_check_dict,
        lint_snapshot=quality_to_dict(lint_result),
        metadata={
            "source_entry_id": entry.get("id"),
            "parsed_entry_id": new_entry.get("id"),
            "entity_id": entry.get("entity_id"),
            "action_id": payload.get("action_id") or action_id_from_entity(entry.get("entity_id")),
            "report_md_rel_path": report_rel_path,
            "evidence_pack_md_rel_path": evidence_rel_path,
            "block_reasons": status_reasons,
            "ticker": ticker,
            "market": _market,
            "claim_evidence_summary": claim_summary,
            "valuation_snapshot": valuation_snapshot,
            "consensus_revision_proxy": consensus_proxy,
            "bear_case_result": bear_case_result,
            "promotion_result": promotion_to_dict(promotion_result),
            "recommendation_candidate": candidate_result,
        },
    )
    record_agent_run(
        conn,
        agent_or_script=SCRIPT_NAME,
        status="success" if not recommendation_status.startswith("blocked") else "blocked",
        entity_type="investment_report_snapshot",
        entity_id=entry["entity_id"],
        data_health_snapshot=freshness_gate.data_health_snapshot,
        freshness_gate_result=gate_to_dict(freshness_gate),
        evidence_check_result=evidence_check_dict,
        lint_result=quality_to_dict(lint_result),
        source_registry_snapshot=src_snapshot,
        output_status=recommendation_status,
        block_reasons=status_reasons,
        metadata={"source_entry_id": entry.get("id"), "parsed_entry_id": new_entry.get("id")},
    )
    return {
        "entity_id": entry["entity_id"],
        "source_entry_id": entry["id"],
        "new_entry_id": new_entry["id"],
        "recommendation_status": recommendation_status,
        "recommendation_state_reasons": status_reasons,
        "dashboard_summary_quality": parsed.get("dashboard_summary_quality"),
        "source_discipline_audit": parsed.get("source_discipline_audit"),
    }


def main():
    parser = argparse.ArgumentParser(description="Parse investment report dashboard summaries")
    parser.add_argument("--action-id")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    conn = connect_db()
    try:
        entries = latest_report_entries(conn, action_id=args.action_id, limit=max(args.limit, 1))
        if not entries:
            if args.allow_empty:
                print("[]")
                return
            raise SystemExit("No investment_report_snapshot entries found")
        results = [parse_entry(conn, entry, dry_run=args.dry_run) for entry in entries]
        if not args.dry_run:
            conn.commit()
        log_run(
            SCRIPT_NAME,
            "success",
            "investment report dashboard summaries parsed",
            {
                "action_id": args.action_id,
                "dry_run": args.dry_run,
                "parsed_count": len(results),
                "results": results[:10],
            },
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
