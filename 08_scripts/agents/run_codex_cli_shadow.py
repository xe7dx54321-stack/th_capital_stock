#!/usr/bin/env python3
"""Run a guarded Codex CLI shadow execution for a system engineering handoff."""

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_handoff, get_profile, load_handoff_source_entry, profile_workspace_path
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "run_codex_cli_shadow.py"
PROJECT_ROOT = project_path()
POLICY_PATH = project_path("00_control", "engineering_autonomy_policy.json")


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="run_codex_cli_shadow.py",
        note="Codex CLI shadow handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for Codex CLI shadow run")
    return entry


def read_rel_path_text(rel_path):
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def preview_text(text, max_chars=12000):
    value = str(text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def ensure_text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def load_policy():
    if not POLICY_PATH.exists():
        return {}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def load_cli_shadow_policy():
    policy = load_policy()
    cli_shadow = policy.get("cli_shadow") or {}
    return {
        "provider": cli_shadow.get("provider") or "codex",
        "enabled": bool(cli_shadow.get("enabled", False)),
        "auto_run": bool(cli_shadow.get("auto_run", False)),
        "mode": cli_shadow.get("mode") or "read_only",
        "timeout_seconds": int(cli_shadow.get("timeout_seconds") or 120),
        "max_request_count": int(cli_shadow.get("max_request_count") or 6),
        "policy_rel_path": relative_to_project(POLICY_PATH),
    }


def summarize_requests(requests, limit=8):
    preview = []
    for item in requests[:limit]:
        preview.append(
            f"- {item.get('family')} / {item.get('gap_type')} / {item.get('ts_code')} / {item.get('priority')}"
        )
    if len(requests) > limit:
        preview.append(f"- ... 其余 {len(requests) - limit} 条请直接查看任务规格文件")
    return preview


def build_prompt(handoff, source_entry):
    payload = source_entry.get("payload", {})
    outputs = handoff.get("outputs") or {}
    task_spec_rel_path = outputs.get("task_spec_rel_path")
    patch_candidate_rel_path = outputs.get("patch_candidate_rel_path")
    validation_plan_rel_path = outputs.get("validation_plan_rel_path")
    policy_rel_path = payload.get("policy_rel_path")
    requests = payload.get("requests") or []

    return "\n".join(
        [
            "你现在扮演受控的系统施工影子执行器。",
            "你的任务不是直接改代码，而是基于当前代码库和任务文件，给出一份高质量、可执行、可审阅的施工建议。",
            "",
            "硬约束：",
            "1. 你可以读取代码和做只读分析。",
            "2. 你不允许修改任何文件。",
            "3. 你不允许执行有副作用的命令。",
            "4. 你不允许声称“已经修好”或“已经提交”。",
            "5. 你必须服从当前工程门禁，所有输出只能停留在候选层。",
            "",
            "请输出以下 6 段：",
            "1. 结论",
            "2. 最小改动方案",
            "3. 需要修改的文件",
            "4. 关键实现点",
            "5. 验证顺序",
            "6. 风险与回滚点",
            "",
            f"handoff_id: {handoff['handoff_id']}",
            f"entity_type: {handoff['entity_type']}",
            f"entity_id: {handoff['entity_id']}",
            f"request_count: {payload.get('request_count') or len(requests)}",
            "",
            "请先读取这些文件：",
            f"1. {task_spec_rel_path or ''}",
            f"2. {patch_candidate_rel_path or ''}",
            f"3. {validation_plan_rel_path or ''}",
            f"4. {policy_rel_path or ''}",
            "",
            "当前请求概览：",
            *summarize_requests(requests),
            "",
            "先自行查阅必要代码和上面 4 个文件，再按 6 段格式给出结果。",
        ]
    )


def should_run_shadow(request_count, shadow_policy, force):
    if force:
        return True, "forced"
    if shadow_policy.get("provider") != "codex":
        return False, "provider_not_codex"
    if not shadow_policy.get("enabled"):
        return False, "policy_disabled"
    if request_count > shadow_policy.get("max_request_count", 0):
        return False, "request_count_exceeds_limit"
    return True, "eligible"


def persist_result(conn, handoff, run_dir, status, reason, returncode, last_message, metadata=None):
    prompt_path = run_dir / "prompt.md"
    stdout_path = run_dir / "stdout.log"
    last_message_path = run_dir / "last_message.md"
    result_path = run_dir / "result.json"
    payload = {
        "prompt_rel_path": relative_to_project(prompt_path) if prompt_path.exists() else None,
        "stdout_rel_path": relative_to_project(stdout_path) if stdout_path.exists() else None,
        "last_message_rel_path": relative_to_project(last_message_path) if last_message_path.exists() else None,
        "result_rel_path": relative_to_project(result_path),
        "returncode": returncode,
        "reason": reason,
        "last_message_preview": preview_text(last_message, max_chars=2000),
    }
    if metadata:
        payload.update(metadata)
    registry_entry = register_snapshot(
        conn,
        entity_type="codex_cli_shadow_run",
        entity_id=handoff["handoff_id"],
        status=status,
        source=SCRIPT_NAME,
        relationships={
            "handoff_id": handoff["handoff_id"],
            "source_entity_type": handoff["entity_type"],
            "source_entity_id": handoff["entity_id"],
        },
        payload=payload,
    )
    return payload, registry_entry


def main():
    parser = argparse.ArgumentParser(description="Run guarded Codex CLI shadow execution")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--timeout-seconds", type=int, help="Override timeout from engineering policy")
    parser.add_argument("--force", action="store_true", help="Bypass request-count gate and force a shadow run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    codex_path = shutil.which("codex")
    if not codex_path:
        raise SystemExit("codex CLI not found in PATH")

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "openclaw_system_exec":
        raise SystemExit("This handoff does not belong to openclaw_system_exec")
    if handoff["entity_type"] != "system_change_request":
        raise SystemExit("This script only supports system_change_request handoffs")
    if handoff.get("status") not in {"accepted", "completed"}:
        raise SystemExit("Please process the system handoff first so task spec / patch candidate exist")

    profile = get_profile("openclaw_system_exec")
    workspace = profile_workspace_path(profile)
    run_dir = workspace / "codex_shadow_runs" / handoff["handoff_id"]
    prompt_path = run_dir / "prompt.md"
    stdout_path = run_dir / "stdout.log"
    last_message_path = run_dir / "last_message.md"
    result_path = run_dir / "result.json"

    conn = sqlite3.connect(DB_PATH)
    source_entry = load_source_entry(conn, handoff)
    shadow_policy = load_cli_shadow_policy()
    payload = source_entry.get("payload", {})
    request_count = int(payload.get("request_count") or len(payload.get("requests") or []))
    timeout_seconds = args.timeout_seconds or shadow_policy.get("timeout_seconds", 120)
    eligible, eligibility_reason = should_run_shadow(request_count, shadow_policy, args.force)
    prompt = build_prompt(handoff, source_entry)
    command = [
        codex_path,
        "exec",
        "--skip-git-repo-check",
        "-s",
        "read-only",
        "-C",
        str(PROJECT_ROOT),
        "-c",
        "model_reasoning_effort=\"medium\"",
        "--color",
        "never",
        "--ephemeral",
        "-o",
        str(last_message_path),
        "-",
    ]

    if args.dry_run:
        print(
            json.dumps(
                {
                    "command": command,
                    "run_dir": str(run_dir),
                    "request_count": request_count,
                    "timeout_seconds": timeout_seconds,
                    "eligible": eligible,
                    "eligibility_reason": eligibility_reason,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        conn.close()
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    result = {
        "handoff_id": handoff["handoff_id"],
        "codex_path": codex_path,
        "timeout_seconds": timeout_seconds,
        "request_count": request_count,
        "eligible": eligible,
        "eligibility_reason": eligibility_reason,
    }

    if not eligible:
        stdout_text = f"shadow skipped: {eligibility_reason}\n"
        stdout_path.write_text(stdout_text, encoding="utf-8")
        result.update({"returncode": None, "status": "skipped"})
        payload, registry_entry = persist_result(
            conn,
            handoff,
            run_dir,
            "skipped",
            eligibility_reason,
            None,
            "",
            {
                "request_count": request_count,
                "timeout_seconds": timeout_seconds,
                "eligibility_reason": eligibility_reason,
            },
        )
    else:
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            stdout_text = (completed.stdout or "") + (completed.stderr or "")
            stdout_path.write_text(stdout_text, encoding="utf-8")
            last_message = last_message_path.read_text(encoding="utf-8") if last_message_path.exists() else ""
            status = "succeeded" if completed.returncode == 0 else "failed"
            result.update({"returncode": completed.returncode, "status": status})
            payload, registry_entry = persist_result(
                conn,
                handoff,
                run_dir,
                status,
                "completed" if completed.returncode == 0 else "non_zero_exit",
                completed.returncode,
                last_message,
                {
                    "request_count": request_count,
                    "timeout_seconds": timeout_seconds,
                    "eligibility_reason": eligibility_reason,
                },
            )
        except subprocess.TimeoutExpired as exc:
            stdout_text = ensure_text(exc.stdout) + ensure_text(exc.stderr)
            stdout_path.write_text(stdout_text, encoding="utf-8")
            last_message = last_message_path.read_text(encoding="utf-8") if last_message_path.exists() else ""
            status = "timeout"
            result.update({"returncode": None, "status": status})
            payload, registry_entry = persist_result(
                conn,
                handoff,
                run_dir,
                status,
                "timeout",
                None,
                last_message,
                {
                    "request_count": request_count,
                    "timeout_seconds": timeout_seconds,
                    "eligibility_reason": eligibility_reason,
                },
            )

    result.update(
        {
            "prompt_rel_path": payload.get("prompt_rel_path"),
            "stdout_rel_path": payload.get("stdout_rel_path"),
            "last_message_rel_path": payload.get("last_message_rel_path"),
        }
    )
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    conn.commit()
    conn.close()

    log_run(
        SCRIPT_NAME,
        "success" if result["status"] == "succeeded" else "warning",
        "Codex CLI shadow run finished",
        {
            "handoff_id": handoff["handoff_id"],
            "returncode": result.get("returncode"),
            "status": result["status"],
            "request_count": request_count,
            "timeout_seconds": timeout_seconds,
            "eligibility_reason": eligibility_reason,
            "registry_entry_id": registry_entry["id"],
            "last_message_rel_path": payload.get("last_message_rel_path"),
        },
    )
    print(f"Codex CLI shadow run: {handoff['handoff_id']}")
    print(f"  status={result['status']}")
    print(f"  request_count={request_count}")
    print(f"  eligibility_reason={eligibility_reason}")
    print(f"  prompt_rel_path={payload.get('prompt_rel_path')}")
    print(f"  stdout_rel_path={payload.get('stdout_rel_path')}")
    if payload.get("last_message_rel_path"):
        print(f"  last_message_rel_path={payload.get('last_message_rel_path')}")


if __name__ == "__main__":
    main()
