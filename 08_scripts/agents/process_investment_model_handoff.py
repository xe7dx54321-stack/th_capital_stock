#!/usr/bin/env python3
"""Process investment analyst/report-writer handoffs through shadow model runtime."""

import argparse
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    DB_PATH,
    ensure_auto_handoff,
    get_handoff,
    get_latest_registry_entry,
    load_handoff_source_entry,
    resolve_handoff,
)
from smr_investment_reports import parse_report_dashboard_payload
from smr_paths import normalize_project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_NAME = "process_investment_model_handoff.py"
SUPPORTED_PROFILE_IDS = {"hermes_investment_analyst", "hermes_investment_report_writer"}


def run_command(command, dry_run=False):
    if dry_run:
        return 0, "(dry-run)"
    completed = subprocess.run(command, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output.strip()


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by=SCRIPT_NAME,
        note="投资模型 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for handoff")
    return entry


def latest_shadow_entry(conn, handoff_id):
    return get_latest_registry_entry(conn, "model_shadow_execution", handoff_id)


def build_packet(handoff_id, dry_run=False):
    command = [
        sys.executable,
        str(SCRIPT_DIR / "build_model_task_packet.py"),
        "--handoff-id",
        handoff_id,
    ]
    if dry_run:
        command.append("--dry-run")
    return run_command(command, dry_run=False)


def run_shadow(handoff_id, dry_run=False):
    command = [
        sys.executable,
        str(SCRIPT_DIR / "run_model_shadow.py"),
        "--handoff-id",
        handoff_id,
    ]
    if dry_run:
        command.append("--dry-run")
    return run_command(command, dry_run=False)


def shadow_succeeded(shadow_entry):
    return (shadow_entry or {}).get("status") == "shadow_call_succeeded"


def model_output_text(shadow_entry):
    rel_path = ((shadow_entry or {}).get("payload") or {}).get("response_text_rel_path")
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    marker = "## Model Output"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def has_substantive_output(handoff, shadow_entry):
    text = model_output_text(shadow_entry)
    if len(text) < 1200:
        return False
    stripped = text.strip()
    if stripped.startswith("$LOAD") or stripped.upper().startswith("LOAD"):
        return False
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()
    if handoff["to_profile_id"] == "hermes_investment_analyst":
        required_terms = ["研究结论", "共识", "分歧", "证伪"]
    else:
        required_terms = ["执行摘要", "调仓", "逻辑分析", "技术分析", "风险", "dashboardsummaryjson"]
    return all(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", term).lower() in normalized for term in required_terms)


def common_candidate_payload(source_entry, shadow_entry, handoff):
    shadow_payload = (shadow_entry or {}).get("payload") or {}
    source_payload = source_entry.get("payload") or {}
    source_relationships = source_entry.get("relationships") or {}
    return {
        "source_entity_type": source_entry.get("entity_type"),
        "source_entity_id": source_entry.get("entity_id"),
        "source_entry_id": source_entry.get("id"),
        "source_status": source_entry.get("status"),
        "handoff_id": handoff["handoff_id"],
        "from_profile_id": handoff["from_profile_id"],
        "to_profile_id": handoff["to_profile_id"],
        "model_shadow_entry_id": (shadow_entry or {}).get("id"),
        "model_shadow_status": (shadow_entry or {}).get("status"),
        "model_response_text_rel_path": shadow_payload.get("response_text_rel_path"),
        "model_result_md_rel_path": shadow_payload.get("result_md_rel_path"),
        "compiled_prompt_rel_path": shadow_payload.get("compiled_prompt_rel_path"),
        "request_json_rel_path": shadow_payload.get("request_json_rel_path"),
        "response_json_rel_path": shadow_payload.get("response_json_rel_path"),
        "provider": shadow_payload.get("provider"),
        "model": shadow_payload.get("model"),
        "requires_human_review": True,
        "source_pack_md_rel_path": source_payload.get("pack_md_rel_path")
        or source_relationships.get("pack_md_rel_path")
        or source_payload.get("evidence_pack_md_rel_path")
        or source_relationships.get("evidence_pack_md_rel_path"),
        "source_pack_json_rel_path": source_payload.get("pack_json_rel_path")
        or source_relationships.get("pack_json_rel_path"),
    }


def register_research_synthesis(conn, handoff, source_entry, shadow_entry):
    payload = common_candidate_payload(source_entry, shadow_entry, handoff)
    entity_id = source_entry["entity_id"]
    entry = register_snapshot(
        conn,
        entity_type="investment_research_synthesis_snapshot",
        entity_id=entity_id,
        status="candidate_from_shadow",
        source=SCRIPT_NAME,
        relationships={
            "evidence_pack_entry_id": source_entry.get("id"),
            "analyst_handoff_id": handoff["handoff_id"],
            "model_shadow_entry_id": shadow_entry.get("id"),
            "model_response_text_rel_path": payload.get("model_response_text_rel_path"),
            "evidence_pack_md_rel_path": payload.get("source_pack_md_rel_path"),
        },
        payload={
            **payload,
            "synthesis_kind": "deep_research_candidate",
            "synthesis_md_rel_path": payload.get("model_response_text_rel_path"),
            "evidence_pack_md_rel_path": payload.get("source_pack_md_rel_path"),
            "quality_boundary": "candidate only; requires human review before dashboard truth layer",
        },
    )
    auto_handoff = ensure_auto_handoff(
        conn,
        entry,
        note="investment research synthesis ready for institutional report writing",
        created_by=SCRIPT_NAME,
    )
    entry["auto_handoff"] = {
        "created": auto_handoff.get("created"),
        "reason": auto_handoff.get("reason"),
        "handoff_id": ((auto_handoff.get("handoff") or {}).get("handoff_id")),
        "to_profile_id": ((auto_handoff.get("handoff") or {}).get("to_profile_id")),
    }
    return entry


def register_investment_report(conn, handoff, source_entry, shadow_entry):
    payload = common_candidate_payload(source_entry, shadow_entry, handoff)
    entity_id = source_entry["entity_id"]
    evidence_pack_rel_path = (
        (source_entry.get("payload") or {}).get("evidence_pack_md_rel_path")
        or (source_entry.get("relationships") or {}).get("evidence_pack_md_rel_path")
        or payload.get("source_pack_md_rel_path")
    )
    dashboard_payload = parse_report_dashboard_payload(
        payload.get("model_response_text_rel_path"),
        evidence_pack_rel_path,
    )
    return register_snapshot(
        conn,
        entity_type="investment_report_snapshot",
        entity_id=entity_id,
        status="candidate_from_shadow",
        source=SCRIPT_NAME,
        relationships={
            "research_synthesis_entry_id": source_entry.get("id"),
            "report_writer_handoff_id": handoff["handoff_id"],
            "model_shadow_entry_id": shadow_entry.get("id"),
            "model_response_text_rel_path": payload.get("model_response_text_rel_path"),
            "synthesis_md_rel_path": (source_entry.get("payload") or {}).get("synthesis_md_rel_path")
            or (source_entry.get("relationships") or {}).get("synthesis_md_rel_path")
            or payload.get("model_response_text_rel_path"),
            "evidence_pack_md_rel_path": evidence_pack_rel_path,
        },
        payload={
            **payload,
            **dashboard_payload,
            "report_kind": "institutional_action_report_candidate",
            "report_md_rel_path": payload.get("model_response_text_rel_path"),
            "evidence_pack_md_rel_path": evidence_pack_rel_path,
            "quality_boundary": "candidate only; requires human review before dashboard truth layer",
        },
    )


def process_successful_shadow(conn, handoff, source_entry, shadow_entry):
    if not has_substantive_output(handoff, shadow_entry):
        return None
    if handoff["to_profile_id"] == "hermes_investment_analyst":
        return register_research_synthesis(conn, handoff, source_entry, shadow_entry)
    if handoff["to_profile_id"] == "hermes_investment_report_writer":
        return register_investment_report(conn, handoff, source_entry, shadow_entry)
    return None


def main():
    parser = argparse.ArgumentParser(description="Process investment model handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--shadow-dry-run", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] not in SUPPORTED_PROFILE_IDS:
        raise SystemExit("This handoff does not belong to an investment model profile")

    conn = sqlite3.connect(DB_PATH)
    try:
        source_entry = load_source_entry(conn, handoff)

        packet_rc, packet_output = build_packet(args.handoff_id, dry_run=args.dry_run)
        if packet_rc != 0:
            raise SystemExit(packet_output or "build_model_task_packet.py failed")

        if args.dry_run:
            print(packet_output)
            log_run(
                SCRIPT_NAME,
                "success",
                "investment model handoff dry-run packet built",
                {
                    "handoff_id": args.handoff_id,
                    "to_profile_id": handoff["to_profile_id"],
                    "entity_type": handoff["entity_type"],
                    "entity_id": handoff["entity_id"],
                    "dry_run": True,
                },
            )
            return

        shadow_rc, shadow_output = run_shadow(args.handoff_id, dry_run=args.dry_run or args.shadow_dry_run)
        if shadow_rc != 0:
            raise SystemExit(shadow_output or "run_model_shadow.py failed")

        candidate_entry = None
        shadow_entry = None
        if not args.dry_run and not args.shadow_dry_run:
            shadow_entry = latest_shadow_entry(conn, args.handoff_id)
            if shadow_succeeded(shadow_entry):
                candidate_entry = process_successful_shadow(conn, handoff, source_entry, shadow_entry)

        outputs = {
            "packet_output": packet_output.splitlines()[:12],
            "shadow_output": shadow_output.splitlines()[:12],
            "model_shadow_entry_id": (shadow_entry or {}).get("id"),
            "model_shadow_status": (shadow_entry or {}).get("status"),
            "candidate_entry_id": (candidate_entry or {}).get("id"),
            "candidate_entity_type": (candidate_entry or {}).get("entity_type"),
            "candidate_entity_id": (candidate_entry or {}).get("entity_id"),
            "auto_handoff": (candidate_entry or {}).get("auto_handoff"),
            "shadow_dry_run": args.shadow_dry_run,
        }

        if args.complete and not args.dry_run:
            status_note = (shadow_entry or {}).get("status") or ("shadow_dry_run" if args.shadow_dry_run else "unknown")
            resolve_handoff(
                conn,
                handoff_id=args.handoff_id,
                status="completed",
                resolved_by=SCRIPT_NAME,
                summary=f"投资模型 handoff 已完成模型任务包和 shadow 执行记录：{status_note}",
                outputs=outputs,
                source=SCRIPT_NAME,
            )

        if not args.dry_run:
            conn.commit()

        log_run(
            SCRIPT_NAME,
            "success",
            "investment model handoff processed",
            {
                "handoff_id": args.handoff_id,
                "to_profile_id": handoff["to_profile_id"],
                "entity_type": handoff["entity_type"],
                "entity_id": handoff["entity_id"],
                "complete": args.complete,
                "dry_run": args.dry_run,
                "shadow_dry_run": args.shadow_dry_run,
                "model_shadow_status": outputs.get("model_shadow_status"),
                "candidate_entry_id": outputs.get("candidate_entry_id"),
            },
        )
        print(f"Investment model handoff processed: {args.handoff_id}")
        print(f"  to_profile_id={handoff['to_profile_id']}")
        print(f"  shadow_status={outputs.get('model_shadow_status') or ('shadow_dry_run' if args.shadow_dry_run else '')}")
        print(f"  candidate_entry_id={outputs.get('candidate_entry_id') or ''}")
        auto_handoff = outputs.get("auto_handoff") or {}
        if auto_handoff:
            print(f"  auto_handoff={auto_handoff.get('reason')} {auto_handoff.get('handoff_id') or ''}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
