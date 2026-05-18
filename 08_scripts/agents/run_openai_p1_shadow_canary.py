#!/usr/bin/env python3
"""Run a controlled OpenAI P1 shadow canary without mutating checked-in runtime config."""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from build_model_task_packet import collect_rel_paths, load_source_entry, read_preview
from smr_agents import DB_PATH, get_handoff, get_profile, list_handoffs, profile_workspace_path
from smr_llm import load_model_profiles, load_task_routes
from smr_paths import project_path, relative_to_project

ROOT = Path(__file__).resolve().parents[2]
BUILD_PACKET_SCRIPT = ROOT / "08_scripts" / "agents" / "build_model_task_packet.py"
RUN_SHADOW_SCRIPT = ROOT / "08_scripts" / "agents" / "run_model_shadow.py"

P1_ENTITY_TYPES = (
    "risk_monitor_snapshot",
    "us_signal_snapshot",
    "daily_reporting_snapshot",
)
P1_TO_PROFILE = {
    "risk_monitor_snapshot": "hermes_risk_curator",
    "us_signal_snapshot": "hermes_research_curator",
    "daily_reporting_snapshot": "hermes_reporting_editor",
}


def run(cmd, env):
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=ROOT)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_canary_runtime(runtime_dir, entity_types):
    profiles = load_model_profiles()
    routes = load_task_routes()

    profiles["global_mode"] = "shadow"
    for provider_name, provider in (profiles.get("providers") or {}).items():
        provider["enabled"] = provider_name == "openai"

    routes["global_mode"] = "shadow"
    allowed_entity_types = set(entity_types)
    for entity_type, route in (routes.get("entity_routes") or {}).items():
        route["packet_mode"] = "shadow" if entity_type in allowed_entity_types else "disabled_canary"

    profiles_path = runtime_dir / "model_profiles.json"
    routes_path = runtime_dir / "task_routes.json"
    write_json(profiles_path, profiles)
    write_json(routes_path, routes)
    return profiles_path, routes_path


def source_document_summary(conn, record):
    try:
        entry = load_source_entry(conn, record)
        rel_paths = collect_rel_paths(record, entry)
        source_documents = [read_preview(rel_path) for rel_path in rel_paths]
    except Exception as exc:
        return {
            "total_rel_paths": 0,
            "existing_count": 0,
            "preview_count": 0,
            "missing_rel_paths": [],
            "error": str(exc),
        }

    return {
        "total_rel_paths": len(rel_paths),
        "existing_count": sum(1 for item in source_documents if item.get("exists")),
        "preview_count": sum(1 for item in source_documents if item.get("preview")),
        "missing_rel_paths": [item.get("rel_path") for item in source_documents if not item.get("exists")],
        "error": None,
    }


def source_document_score(summary, recency_rank):
    return (
        int((summary or {}).get("existing_count", 0) > 0),
        (summary or {}).get("existing_count", 0),
        (summary or {}).get("preview_count", 0),
        (summary or {}).get("total_rel_paths", 0),
        -recency_rank,
    )


def latest_completed_handoffs(entity_types):
    selected = {}
    scores = {}
    conn = sqlite3.connect(DB_PATH)
    try:
        for recency_rank, record in enumerate(list_handoffs(status="completed", limit=500)):
            entity_type = record.get("entity_type")
            if entity_type not in entity_types:
                continue
            if record.get("to_profile_id") != P1_TO_PROFILE.get(entity_type):
                continue
            summary = source_document_summary(conn, record)
            candidate = dict(record)
            candidate["source_document_summary"] = summary
            score = source_document_score(summary, recency_rank)
            if entity_type not in selected or score > scores[entity_type]:
                selected[entity_type] = candidate
                scores[entity_type] = score
    finally:
        conn.close()
    return selected


def resolve_target_handoffs(explicit_handoff_ids, entity_types):
    if explicit_handoff_ids:
        conn = sqlite3.connect(DB_PATH)
        records = []
        try:
            for handoff_id in explicit_handoff_ids:
                record = get_handoff(handoff_id)
                entity_type = record.get("entity_type")
                if entity_type not in entity_types:
                    raise SystemExit(
                        f"handoff 不在本次 P1 canary 范围内: {handoff_id} ({entity_type})"
                    )
                expected_profile = P1_TO_PROFILE.get(entity_type)
                if record.get("to_profile_id") != expected_profile:
                    raise SystemExit(
                        f"handoff 目标 profile 不符合 P1 约束: {handoff_id} -> {record.get('to_profile_id')}"
                    )
                record["source_document_summary"] = source_document_summary(conn, record)
                records.append(record)
        finally:
            conn.close()
        return records, []

    latest = latest_completed_handoffs(entity_types)
    missing = [entity_type for entity_type in entity_types if entity_type not in latest]
    return list(latest.values()), missing


def packet_path_for_handoff(record):
    profile = get_profile(record["to_profile_id"])
    workspace = profile_workspace_path(profile)
    return workspace / "model_packets" / f"{record['handoff_id']}.json"


def response_path_for_handoff(record):
    profile = get_profile(record["to_profile_id"])
    workspace = profile_workspace_path(profile)
    return workspace / "shadow_runs" / f"{record['handoff_id']}__response.json"


def extract_provider_error(summary_payload):
    response_payload = summary_payload.get("response_payload")
    error_text = summary_payload.get("error") or ""

    code = summary_payload.get("provider_error_code")
    reason = summary_payload.get("provider_error_reason")
    message = error_text

    if isinstance(response_payload, dict):
        error_obj = response_payload.get("error") if isinstance(response_payload.get("error"), dict) else {}
        code = code or error_obj.get("code") or response_payload.get("code")
        reason = reason or error_obj.get("reason") or response_payload.get("reason")
        message = (
            error_obj.get("message")
            or response_payload.get("message")
            or message
        )

    if message and not isinstance(message, str):
        message = json.dumps(message, ensure_ascii=False)
    if not reason and message:
        match = re.search(r'reason="?([A-Z0-9_]+)"?', message)
        if match:
            reason = match.group(1)

    return {
        "code": code,
        "reason": reason,
        "message": message,
    }


def is_quota_exhausted(http_status, error_detail):
    message = (error_detail.get("message") or "").lower()
    quota_codes = {"USAGE_LIMIT_EXCEEDED", "INSUFFICIENT_QUOTA"}
    quota_reasons = {
        "DAILY_LIMIT_EXCEEDED",
        "MONTHLY_LIMIT_EXCEEDED",
        "QUOTA_EXCEEDED",
        "INSUFFICIENT_QUOTA",
    }
    if (error_detail.get("code") or "") in quota_codes:
        return True
    if (error_detail.get("reason") or "") in quota_reasons:
        return True
    return http_status == 429 and (
        "daily usage limit exceeded" in message
        or "usage limit exceeded" in message
        or "insufficient quota" in message
    )


def summarize_response(record):
    response_path = response_path_for_handoff(record)
    if not response_path.exists():
        return {
            "handoff_id": record["handoff_id"],
            "entity_type": record["entity_type"],
            "response_json_rel_path": relative_to_project(response_path),
            "execution_status": "missing_response_json",
            "gate_status": None,
            "http_status": None,
            "error": "response.json not found",
        }

    payload = json.loads(response_path.read_text(encoding="utf-8"))
    error_detail = extract_provider_error(payload)
    return {
        "handoff_id": record["handoff_id"],
        "entity_type": record["entity_type"],
        "response_json_rel_path": relative_to_project(response_path),
        "gate_status": payload.get("gate_status"),
        "execution_status": payload.get("execution_status"),
        "http_status": payload.get("http_status"),
        "error": error_detail.get("message"),
        "provider_error_code": error_detail.get("code"),
        "provider_error_reason": error_detail.get("reason"),
        "quota_exhausted": is_quota_exhausted(payload.get("http_status"), error_detail),
    }


def print_plan(records, missing):
    print("OpenAI P1 shadow canary 计划")
    for record in records:
        source_summary = record.get("source_document_summary") or {}
        print(
            f"- handoff: {record['handoff_id']} | entity_type={record['entity_type']} | "
            f"entity_id={record['entity_id']} | to_profile={record['to_profile_id']} | status={record['status']}"
        )
        print(
            "  "
            f"source_docs={source_summary.get('existing_count', 0)}/{source_summary.get('total_rel_paths', 0)} | "
            f"preview_docs={source_summary.get('preview_count', 0)}"
        )
        if source_summary.get("error"):
            print(f"  source_doc_error={source_summary['error']}")
        elif source_summary.get("missing_rel_paths"):
            print(f"  missing_rel_paths={', '.join(source_summary['missing_rel_paths'])}")
    if missing:
        print(f"- 缺少已完成 handoff 的 entity_type: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description="Run controlled OpenAI P1 shadow canary")
    parser.add_argument(
        "--handoff-id",
        action="append",
        default=[],
        help="指定要跑的 handoff；默认自动选择每个 P1 entity_type 最新 completed handoff",
    )
    parser.add_argument(
        "--entity-type",
        action="append",
        choices=P1_ENTITY_TYPES,
        default=[],
        help="限制自动选择的 P1 entity_type；默认是 risk/us_signal/daily_reporting 三条",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--continue-on-quota-exhausted",
        action="store_true",
        help="即使检测到额度耗尽类 429，也继续尝试后续 handoff",
    )
    args = parser.parse_args()

    entity_types = args.entity_type or list(P1_ENTITY_TYPES)
    records, missing = resolve_target_handoffs(args.handoff_id, entity_types)
    if not records:
        raise SystemExit("没有找到可执行的 P1 handoff")

    print_plan(records, missing)
    if args.dry_run:
        return

    with tempfile.TemporaryDirectory(prefix="smr-openai-p1-canary-") as tmp:
        runtime_dir = Path(tmp) / "runtime"
        profiles_path, routes_path = build_canary_runtime(runtime_dir, entity_types)

        env = os.environ.copy()
        env["SMR_MODEL_PROFILES_PATH"] = str(profiles_path)
        env["SMR_TASK_ROUTES_PATH"] = str(routes_path)

        print("")
        print("临时运行时覆盖")
        print(f"- model_profiles: {profiles_path}")
        print(f"- task_routes: {routes_path}")

        summaries = []
        skipped_records = []
        for record in records:
            handoff_id = record["handoff_id"]
            print("")
            print(f"[build_model_task_packet] {handoff_id}")
            rc, out, err = run(
                ["python3", str(BUILD_PACKET_SCRIPT), "--handoff-id", handoff_id],
                env,
            )
            print(out or err)
            if rc != 0:
                raise SystemExit(f"build_model_task_packet 失败: {handoff_id}")

            packet_path = packet_path_for_handoff(record)
            print(f"- packet_json_rel_path: {relative_to_project(packet_path)}")

            print(f"[run_model_shadow] {handoff_id}")
            rc, out, err = run(
                ["python3", str(RUN_SHADOW_SCRIPT), "--handoff-id", handoff_id],
                env,
            )
            print(out or err)
            if rc != 0:
                raise SystemExit(f"run_model_shadow 失败: {handoff_id}")

            summary = summarize_response(record)
            summaries.append(summary)
            if summary.get("quota_exhausted") and not args.continue_on_quota_exhausted:
                skipped_records = records[len(summaries) :]
                print("- 检测到 provider 配额/日限额类错误，后续 handoff 将停止执行，避免继续撞上游额度。")
                break

        print("")
        print("Canary 结果")
        for summary in summaries:
            print(
                f"- {summary['handoff_id']} | entity_type={summary['entity_type']} | "
                f"gate_status={summary['gate_status']} | execution_status={summary['execution_status']} | "
                f"http_status={summary['http_status']}"
            )
            if summary.get("provider_error_code"):
                print(f"  provider_error_code={summary['provider_error_code']}")
            if summary.get("provider_error_reason"):
                print(f"  provider_error_reason={summary['provider_error_reason']}")
            if summary.get("error"):
                print(f"  error={summary['error']}")
            print(f"  response_json_rel_path={summary['response_json_rel_path']}")
        if skipped_records:
            print("- 因额度型错误未继续执行的 handoff:")
            for record in skipped_records:
                print(
                    f"  {record['handoff_id']} | entity_type={record['entity_type']} | "
                    f"entity_id={record['entity_id']} | to_profile={record['to_profile_id']}"
                )


if __name__ == "__main__":
    main()
