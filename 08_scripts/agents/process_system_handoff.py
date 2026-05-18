#!/usr/bin/env python3
"""Process system engineering handoffs into candidate task specs and validation plans."""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    DB_PATH,
    get_handoff,
    get_profile,
    load_handoff_source_entry,
    profile_workspace_path,
    resolve_handoff,
)
from smr_paths import normalize_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "process_system_handoff.py"
SCRIPT_DIR = Path(__file__).resolve().parent


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="process_system_handoff.py",
        note="系统施工 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for system handoff")
    return entry


def load_policy(rel_path):
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_gates(policy):
    gates = policy.get("gates") or {}
    if not gates:
        return []
    return [
        f"allow_auto_code_write={gates.get('allow_auto_code_write', False)}",
        f"allow_auto_test_execution={gates.get('allow_auto_test_execution', False)}",
        f"allow_auto_commit_to_branch={gates.get('allow_auto_commit_to_branch', False)}",
        f"allow_auto_commit_to_main={gates.get('allow_auto_commit_to_main', False)}",
        f"require_green_tests_before_commit={gates.get('require_green_tests_before_commit', False)}",
        f"require_human_review_before_commit={gates.get('require_human_review_before_commit', False)}",
    ]


def collect_file_targets(requests):
    targets = {}
    for item in requests:
        reason = f"{item['family']} / {item['gap_type']} / {item['ts_code']}"
        for rel_path in item.get("suggested_files") or []:
            entry = targets.setdefault(rel_path, {"rel_path": rel_path, "reasons": [], "families": set()})
            entry["reasons"].append(reason)
            entry["families"].add(item["family"])
    return sorted(targets.values(), key=lambda item: item["rel_path"])


def validation_commands(item):
    family = item.get("family")
    target_key = None
    for evidence in item.get("evidence") or []:
        if evidence.get("target_key"):
            target_key = evidence["target_key"]
            break

    commands = [
        "python3 -m py_compile 08_scripts/lib/smr_agents.py 08_scripts/agents/build_system_change_request_snapshot.py 08_scripts/agents/process_system_handoff.py"
    ]
    if family == "public_transcript" and target_key:
        commands.append(f"python3 08_scripts/wiki/fetch_public_transcripts_fool.py --target-key {target_key}")
    elif family == "public_analyst_signal" and target_key:
        commands.append(f"python3 08_scripts/wiki/fetch_marketscreener_analyst_signals.py --target-key {target_key}")
    elif family == "official_material":
        entity_id = item.get("entity_id") or item.get("ts_code")
        if target_key:
            commands.append(f"python3 08_scripts/wiki/fetch_ir_primary_materials.py --target-key {target_key}")
            commands.append(f"python3 08_scripts/wiki/fetch_sec_official_materials.py --target-key {target_key}")
        elif entity_id:
            commands.append(f"python3 08_scripts/wiki/fetch_ir_primary_materials.py --entity-id {entity_id}")
            commands.append(f"python3 08_scripts/wiki/fetch_sec_official_materials.py --entity-id {entity_id}")
    commands.append("python3 08_scripts/wiki/build_source_manifest.py")
    return commands


def render_task_spec(handoff, entry, policy):
    payload = entry.get("payload", {})
    requests = payload.get("requests") or []
    lines = [
        f"# 系统施工任务规格：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- request_count: `{len(requests)}`",
        f"- focus_strategy: `{payload.get('focus_strategy') or ''}`",
        "",
        "## 当前门禁",
        "",
    ]
    for gate_line in summarize_gates(policy):
        lines.append(f"- {gate_line}")
    lines.extend(
        [
            "",
            "## 施工任务",
            "",
        ]
    )
    for index, item in enumerate(requests, start=1):
        lines.extend(
            [
                f"### {index}. {item['name']} / {item['ts_code']}",
                "",
                f"- family: `{item['family']}`",
                f"- gap_type: `{item['gap_type']}`",
                f"- priority: `{item['priority']}`",
                f"- summary: {item['summary']}",
                "",
                "#### 施工动作",
                "",
            ]
        )
        for text in item.get("required_work") or []:
            lines.append(f"- {text}")
        lines.extend(
            [
                "",
                "#### 验收口径",
                "",
            ]
        )
        for text in item.get("acceptance_checks") or []:
            lines.append(f"- {text}")
        lines.extend(
            [
                "",
                "#### 证据锚点",
                "",
            ]
        )
        for evidence in item.get("evidence") or []:
            lines.append(f"- `{evidence.get('type')}`: {json.dumps(evidence, ensure_ascii=False, sort_keys=True)}")
        lines.append("")
    return "\n".join(lines)


def render_patch_candidate(handoff, entry, policy):
    payload = entry.get("payload", {})
    requests = payload.get("requests") or []
    targets = collect_file_targets(requests)
    lines = [
        f"# 系统补丁候选：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        "- apply_mode: `review_only`",
        f"- allow_auto_code_write: `{(policy.get('gates') or {}).get('allow_auto_code_write', False)}`",
        f"- allow_auto_commit_to_branch: `{(policy.get('gates') or {}).get('allow_auto_commit_to_branch', False)}`",
        "",
        "## 建议改动边界",
        "",
    ]
    if not targets:
        lines.append("- 当前没有收敛出明确文件边界，需要先人工补充。")
        lines.append("")
    else:
        for target in targets:
            lines.extend(
                [
                    f"### {target['rel_path']}",
                    "",
                    f"- families: `{','.join(sorted(target['families']))}`",
                    "- reasons:",
                ]
            )
            for reason in target["reasons"]:
                lines.append(f"  - {reason}")
            lines.append("")
    lines.extend(
        [
            "## 候选补丁原则",
            "",
            "- 先修注册表、匹配规则和抓取路径，不因为单点缺口去重构整套 runtime。",
            "- 所有代码改动先停留在候选层，等验证通过和人工审核后再考虑进入 commit candidate。",
            "- 如果只是源本身阶段性没有新内容，要把结论写成“源暂不可得”，而不是伪造覆盖成功。",
            "",
        ]
    )
    return "\n".join(lines)


def render_validation_plan(handoff, entry):
    payload = entry.get("payload", {})
    requests = payload.get("requests") or []
    lines = [
        f"# 系统验证计划：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- request_count: `{len(requests)}`",
        "",
        "## 最小验证清单",
        "",
    ]
    if not requests:
        lines.append("- 当前没有待验证请求。")
        lines.append("")
        return "\n".join(lines)

    for index, item in enumerate(requests, start=1):
        lines.extend(
            [
                f"### {index}. {item['name']} / {item['ts_code']}",
                "",
            ]
        )
        for command in validation_commands(item):
            lines.append(f"- `{command}`")
        lines.extend(
            [
                "",
                "#### 通过标准",
                "",
            ]
        )
        for text in item.get("acceptance_checks") or []:
            lines.append(f"- {text}")
        lines.append("")
    return "\n".join(lines)


def render_verification_stub(handoff, entry):
    payload = entry.get("payload", {})
    requests = payload.get("requests") or []
    lines = [
        f"# 系统验证留痕：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        "- status: `pending_execution`",
        "",
        "## 待补记录",
        "",
    ]
    for item in requests:
        lines.append(f"- `{item['task_key']}`: 待跑验证命令，待记录结果。")
    lines.append("")
    return "\n".join(lines)


def codex_shadow_policy(policy):
    config = policy.get("cli_shadow") or {}
    return {
        "provider": config.get("provider") or "codex",
        "enabled": bool(config.get("enabled", False)),
        "auto_run": bool(config.get("auto_run", False)),
        "timeout_seconds": int(config.get("timeout_seconds") or 120),
    }


def run_codex_shadow_if_enabled(handoff_id, policy):
    config = codex_shadow_policy(policy)
    if not config["enabled"] or not config["auto_run"] or config["provider"] != "codex":
        return {"requested": False, "reason": "policy_disabled_or_not_codex", "output": ""}

    command = [
        sys.executable,
        str(SCRIPT_DIR / "run_codex_cli_shadow.py"),
        "--handoff-id",
        handoff_id,
        "--timeout-seconds",
        str(config["timeout_seconds"]),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    output = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return {
        "requested": True,
        "reason": "launched" if completed.returncode == 0 else "launcher_failed",
        "returncode": completed.returncode,
        "output": output,
    }


def main():
    parser = argparse.ArgumentParser(description="Process engineering handoff into candidate artifacts")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--complete", action="store_true", help="Complete handoff after artifact generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "openclaw_system_exec":
        raise SystemExit("This handoff does not belong to openclaw_system_exec")
    if handoff["entity_type"] != "system_change_request":
        raise SystemExit("This script only supports system_change_request handoffs")

    profile = get_profile("openclaw_system_exec")
    workspace = profile_workspace_path(profile)
    task_spec_dir = workspace / "task_specs"
    patch_dir = workspace / "patch_candidates"
    test_dir = workspace / "test_runs"
    stem = f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}"
    task_spec_path = task_spec_dir / f"{stem}.md"
    patch_path = patch_dir / f"{stem}.md"
    validation_path = test_dir / f"{stem}__validation_plan.md"
    verification_path = test_dir / f"{stem}__verification_stub.md"

    conn = sqlite3.connect(DB_PATH)
    entry = load_source_entry(conn, handoff)
    policy = load_policy(entry.get("payload", {}).get("policy_rel_path"))
    payload = entry.get("payload", {})
    request_keys = [item.get("task_key") for item in payload.get("requests") or [] if item.get("task_key")]

    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"task_spec_rel_path: {relative_to_project(task_spec_path)}")
        print(f"patch_candidate_rel_path: {relative_to_project(patch_path)}")
        print(f"validation_plan_rel_path: {relative_to_project(validation_path)}")
        print(f"verification_summary_rel_path: {relative_to_project(verification_path)}")
        conn.close()
        return

    task_spec_dir.mkdir(parents=True, exist_ok=True)
    patch_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    task_spec_path.write_text(render_task_spec(handoff, entry, policy) + "\n", encoding="utf-8")
    patch_path.write_text(render_patch_candidate(handoff, entry, policy) + "\n", encoding="utf-8")
    validation_path.write_text(render_validation_plan(handoff, entry) + "\n", encoding="utf-8")
    verification_path.write_text(render_verification_stub(handoff, entry) + "\n", encoding="utf-8")

    patch_entry = register_snapshot(
        conn,
        entity_type="system_patch_candidate",
        entity_id=stem,
        status="prepared",
        source=SCRIPT_NAME,
        relationships={
            "handoff_id": handoff["handoff_id"],
            "source_entity_type": handoff["entity_type"],
            "source_entity_id": handoff["entity_id"],
        },
        payload={
            "task_spec_rel_path": relative_to_project(task_spec_path),
            "patch_candidate_rel_path": relative_to_project(patch_path),
            "validation_plan_rel_path": relative_to_project(validation_path),
            "verification_summary_rel_path": relative_to_project(verification_path),
            "source_entry_id": entry["id"],
            "request_count": len(request_keys),
            "request_keys": request_keys,
        },
    )
    validation_entry = register_snapshot(
        conn,
        entity_type="system_validation_snapshot",
        entity_id=stem,
        status="planned",
        source=SCRIPT_NAME,
        relationships={
            "handoff_id": handoff["handoff_id"],
            "system_patch_candidate_entry_id": patch_entry["id"],
            "system_patch_candidate_entity_id": patch_entry["entity_id"],
        },
        payload={
            "validation_plan_rel_path": relative_to_project(validation_path),
            "verification_summary_rel_path": relative_to_project(verification_path),
            "request_count": len(request_keys),
            "request_keys": request_keys,
        },
    )

    outputs = {
        "task_spec_rel_path": relative_to_project(task_spec_path),
        "patch_candidate_rel_path": relative_to_project(patch_path),
        "validation_plan_rel_path": relative_to_project(validation_path),
        "verification_summary_rel_path": relative_to_project(verification_path),
        "system_patch_candidate_entry_id": patch_entry["id"],
        "system_validation_entry_id": validation_entry["id"],
        "request_count": len(request_keys),
    }
    record = resolve_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        status="completed" if args.complete else "accepted",
        resolved_by="openclaw_system_exec",
        summary="系统工程 handoff 已生成任务规格、补丁候选和验证计划。",
        outputs=outputs,
        source=SCRIPT_NAME,
    )
    conn.commit()
    conn.close()
    codex_shadow = run_codex_shadow_if_enabled(handoff["handoff_id"], policy)

    log_run(
        SCRIPT_NAME,
        "success",
        "system engineering handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_id": handoff["entity_id"],
            "task_spec_rel_path": outputs["task_spec_rel_path"],
            "patch_candidate_rel_path": outputs["patch_candidate_rel_path"],
            "validation_plan_rel_path": outputs["validation_plan_rel_path"],
            "handoff_status": record["status"],
            "request_count": len(request_keys),
            "codex_shadow_requested": codex_shadow["requested"],
            "codex_shadow_reason": codex_shadow["reason"],
        },
    )
    print(f"Processed system handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  task_spec_rel_path={outputs['task_spec_rel_path']}")
    print(f"  patch_candidate_rel_path={outputs['patch_candidate_rel_path']}")
    print(f"  validation_plan_rel_path={outputs['validation_plan_rel_path']}")
    print(f"  codex_shadow={codex_shadow['reason']}")
    if codex_shadow["output"]:
        for line in codex_shadow["output"].splitlines()[:6]:
            print(f"    {line}")


if __name__ == "__main__":
    main()
