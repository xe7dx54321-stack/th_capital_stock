#!/usr/bin/env python3
"""Build a non-executing model task packet from an existing SMR handoff."""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_handoff, get_profile, load_handoff_source_entry, profile_workspace_path
from smr_llm import resolve_model_route
from smr_paths import normalize_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="build_model_task_packet.py",
        note="模型任务包 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for model task packet")
    return entry


def unique_rel_paths(values):
    seen = set()
    results = []
    for value in values:
        if value in (None, ""):
            continue
        if value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def collect_rel_paths(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    entity_type = handoff["entity_type"]

    mapping = {
        "dynamic_pool_snapshot": [
            relationships.get("snapshot_rel_path"),
            payload.get("snapshot_rel_path"),
        ],
        "stock_objective_monitor_snapshot": [
            relationships.get("monitor_rel_path"),
            payload.get("monitor_rel_path"),
        ],
        "strategy_watch_batch": [
            relationships.get("summary_rel_path"),
            relationships.get("objective_monitor_rel_path"),
            payload.get("summary_rel_path"),
            *(payload.get("card_rel_paths") or []),
        ],
        "trend_research_batch": [
            payload.get("summary_rel_path"),
            payload.get("industry_card_rel_path"),
            *(payload.get("stock_card_rel_paths") or []),
        ],
        "research_quality_snapshot": [
            relationships.get("output_rel_path"),
            payload.get("output_rel_path"),
        ],
        "rotation_candidate_snapshot": [
            relationships.get("summary_rel_path"),
            payload.get("summary_rel_path"),
        ],
        "rotation_execution_plan_snapshot": [
            relationships.get("summary_rel_path"),
            relationships.get("rotation_snapshot_rel_path"),
            payload.get("summary_rel_path"),
        ],
        "portfolio_action_memo_snapshot": [
            relationships.get("summary_rel_path"),
            relationships.get("objective_monitor_rel_path"),
            relationships.get("strategy_watch_rel_path"),
            relationships.get("rotation_snapshot_rel_path"),
            relationships.get("execution_plan_rel_path"),
            payload.get("summary_rel_path"),
        ],
        "investment_evidence_pack_snapshot": [
            relationships.get("pack_md_rel_path"),
            relationships.get("pack_json_rel_path"),
            payload.get("pack_md_rel_path"),
            payload.get("pack_json_rel_path"),
        ],
        "investment_research_synthesis_snapshot": [
            relationships.get("synthesis_md_rel_path"),
            relationships.get("synthesis_json_rel_path"),
            relationships.get("model_response_text_rel_path"),
            relationships.get("evidence_pack_md_rel_path"),
            payload.get("synthesis_md_rel_path"),
            payload.get("synthesis_json_rel_path"),
            payload.get("model_response_text_rel_path"),
            payload.get("evidence_pack_md_rel_path"),
        ],
        "investment_report_snapshot": [
            relationships.get("report_md_rel_path"),
            relationships.get("summary_json_rel_path"),
            relationships.get("model_response_text_rel_path"),
            payload.get("report_md_rel_path"),
            payload.get("summary_json_rel_path"),
            payload.get("model_response_text_rel_path"),
        ],
        "us_signal_snapshot": [
            relationships.get("signal_file_rel_path"),
            payload.get("signal_file_rel_path"),
        ],
        "risk_monitor_snapshot": [
            relationships.get("alert_file_rel_path"),
            payload.get("alert_file_rel_path"),
        ],
        "portfolio_pnl_snapshot": [],
        "daily_reporting_snapshot": [
            relationships.get("latest_report_rel_path"),
            relationships.get("dispatch_board_rel_path"),
            payload.get("latest_report_rel_path"),
            payload.get("dispatch_board_rel_path"),
        ],
        "research_context_note": [
            payload.get("note_rel_path"),
        ],
        "risk_update_candidate": [
            payload.get("note_rel_path"),
            payload.get("risk_candidate_rel_path"),
        ],
        "review_queue": [
            relationships.get("export_rel_path"),
            payload.get("export_rel_path"),
        ],
        "system_change_request": [
            relationships.get("summary_rel_path"),
            relationships.get("policy_rel_path"),
            payload.get("summary_rel_path"),
            payload.get("policy_rel_path"),
        ],
        "wiki_draft": [
            payload.get("source_rel_path"),
        ],
    }
    return unique_rel_paths(mapping.get(entity_type, []))


def read_preview(rel_path, max_lines=16, max_chars=1600):
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return {"rel_path": rel_path, "exists": False, "preview": ""}
    text = path.read_text(encoding="utf-8")
    preview = "\n".join(text.splitlines()[:max_lines]).strip()
    if len(preview) > max_chars:
        preview = preview[: max_chars - 3].rstrip() + "..."
    return {"rel_path": rel_path, "exists": True, "preview": preview}


def source_preview_budget(entity_type):
    if entity_type in {
        "investment_evidence_pack_snapshot",
        "investment_research_synthesis_snapshot",
        "investment_report_snapshot",
    }:
        return {"max_lines": 520, "max_chars": 36000}
    return {"max_lines": 16, "max_chars": 1600}


def sanitize(value):
    return str(value).replace("/", "__").replace(":", "_")


def render_packet_markdown(packet):
    route = packet["model_route"]
    lines = [
        f"# 模型任务包：{packet['packet_id']}",
        "",
        f"- generated_at: `{packet['generated_at']}`",
        f"- handoff_id: `{packet['handoff']['handoff_id']}`",
        f"- handoff_status: `{packet['handoff']['status']}`",
        f"- entity_type: `{packet['handoff']['entity_type']}`",
        f"- entity_id: `{packet['handoff']['entity_id']}`",
        f"- to_profile_id: `{packet['handoff']['to_profile_id']}`",
        "",
        "## 模型路由",
        "",
        f"- route_status: `{route['route_status']}`",
        f"- global_mode: `{route['global_mode']}`",
        f"- route_global_mode: `{route['route_global_mode']}`",
        f"- packet_mode: `{route['packet_mode']}`",
        f"- task_kind: `{route['task_kind'] or ''}`",
        f"- model_slot: `{route['model_slot'] or ''}`",
        f"- provider: `{route['provider'] or ''}`",
        f"- model: `{route['model'] or ''}`",
        f"- reasoning_effort: `{route['reasoning_effort'] or ''}`",
        f"- prompt_pack_rel_path: `{route['prompt_pack_rel_path'] or ''}`",
        f"- requires_human_review: `{route['requires_human_review']}`",
        f"- auto_apply: `{route['auto_apply']}`",
        f"- output_contract: `{route['output_contract'] or ''}`",
        "",
        "## Provider 就绪度",
        "",
        f"- provider_enabled: `{route['provider_readiness'].get('enabled', False)}`",
        f"- api_key_env: `{route['provider_readiness'].get('api_key_env') or ''}`",
        f"- api_key_present: `{route['provider_readiness'].get('has_api_key', False)}`",
        f"- base_url_env: `{route['provider_readiness'].get('base_url_env') or ''}`",
        f"- base_url_present: `{route['provider_readiness'].get('has_base_url', False)}`",
        "",
        "## 源文件",
        "",
    ]

    if not packet["source_documents"]:
        lines.append("- 当前没有抽取到 source files（源文件）路径。")
        lines.append("")

    for item in packet["source_documents"]:
        lines.extend(
            [
                f"### {item['rel_path']}",
                "",
                f"- exists: `{item['exists']}`",
                "",
            ]
        )
        if item["preview"]:
            lines.append("```text")
            lines.append(item["preview"])
            lines.append("```")
            lines.append("")

    lines.extend(
        [
            "## 安全边界",
            "",
            "- 当前任务包只用于后续模型接入，不代表已经允许真实模型调用。",
            "- 当前任务包只允许进入候选层，不允许直接改真相层。",
            "- 高风险动作仍需人工审核。",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build a model task packet from an SMR handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    conn = sqlite3.connect(DB_PATH)
    entry = load_source_entry(conn, handoff)
    route = resolve_model_route(handoff["entity_type"], handoff.get("to_profile_id"))

    profile = get_profile(handoff["to_profile_id"])
    workspace = profile_workspace_path(profile)
    packet_dir = workspace / "model_packets"
    stem = sanitize(args.handoff_id)
    packet_json_path = packet_dir / f"{stem}.json"
    packet_md_path = packet_dir / f"{stem}.md"

    rel_paths = collect_rel_paths(handoff, entry)
    preview_budget = source_preview_budget(handoff["entity_type"])
    source_documents = [read_preview(rel_path, **preview_budget) for rel_path in rel_paths]
    packet = {
        "packet_id": stem,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "handoff": {
            "handoff_id": handoff["handoff_id"],
            "status": handoff["status"],
            "handoff_type": handoff["handoff_type"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "from_profile_id": handoff["from_profile_id"],
            "to_profile_id": handoff["to_profile_id"],
            "required_action": handoff["required_action"],
        },
        "source_entry": {
            "id": entry["id"],
            "status": entry["status"],
            "source": entry["source"],
            "created_at": entry["created_at"],
            "snapshot_index": entry["snapshot_index"],
        },
        "model_route": route,
        "source_documents": source_documents,
    }

    if args.dry_run:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
        conn.close()
        return

    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet_md_path.write_text(render_packet_markdown(packet) + "\n", encoding="utf-8")

    registry_entry = register_snapshot(
        conn,
        entity_type="model_task_packet",
        entity_id=handoff["handoff_id"],
        status="generated",
        source="build_model_task_packet.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "to_profile_id": handoff["to_profile_id"],
        },
        payload={
            "packet_json_rel_path": relative_to_project(packet_json_path),
            "packet_md_rel_path": relative_to_project(packet_md_path),
            "route_status": route["route_status"],
            "model_slot": route["model_slot"],
            "provider": route["provider"],
            "model": route["model"],
            "prompt_pack_rel_path": route["prompt_pack_rel_path"],
            "source_document_count": len(source_documents),
            "provider_enabled": route["provider_readiness"].get("enabled", False),
            "api_key_present": route["provider_readiness"].get("has_api_key", False),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "build_model_task_packet.py",
        "success",
        "model task packet built",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "packet_json_rel_path": relative_to_project(packet_json_path),
            "packet_md_rel_path": relative_to_project(packet_md_path),
            "route_status": route["route_status"],
            "model_slot": route["model_slot"],
            "provider": route["provider"],
            "registry_entry_id": registry_entry["id"],
        },
    )
    print(f"Model task packet: {packet_json_path}")
    print(f"  packet_md_rel_path={relative_to_project(packet_md_path)}")
    print(f"  route_status={route['route_status']}")
    print(f"  provider={route['provider'] or ''}")
    print(f"  model={route['model'] or ''}")


if __name__ == "__main__":
    main()
