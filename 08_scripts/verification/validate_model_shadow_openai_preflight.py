#!/usr/bin/env python3
"""Sandbox validation for OpenAI shadow preflight without a real API key."""

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_SHADOW_SCRIPT = ROOT / "08_scripts" / "agents" / "run_model_shadow.py"


def run(cmd, env, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd or ROOT)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def copy_tree(src_root, dst_root, rel_path):
    src = src_root / rel_path
    if not src.exists():
        return
    dst = dst_root / rel_path
    shutil.copytree(src, dst, dirs_exist_ok=True)


def prepare_sandbox_root(tmp_root):
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/profiles"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/model_runtime"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/prompt_packs"))
    (tmp_root / "01_data" / "db").mkdir(parents=True, exist_ok=True)
    sqlite3.connect(tmp_root / "01_data" / "db" / "smr.db").close()


def configure_shadow_runtime(tmp_root):
    model_profiles_path = tmp_root / "12_smr_agents" / "model_runtime" / "model_profiles.json"
    task_routes_path = tmp_root / "12_smr_agents" / "model_runtime" / "task_routes.json"

    model_profiles = json.loads(model_profiles_path.read_text(encoding="utf-8"))
    model_profiles["global_mode"] = "shadow"
    model_profiles["providers"]["openai"]["enabled"] = True
    model_profiles_path.write_text(json.dumps(model_profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    task_routes = json.loads(task_routes_path.read_text(encoding="utf-8"))
    task_routes["global_mode"] = "shadow"
    task_routes_path.write_text(json.dumps(task_routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_preflight_assets(tmp_root):
    handoff_id = "handoff_openai_shadow_preflight"
    handoff_path = tmp_root / "12_smr_agents" / "handoffs" / f"{handoff_id}.json"
    packet_path = (
        tmp_root
        / "12_smr_agents"
        / "workspaces"
        / "hermes_research_curator"
        / "model_packets"
        / f"{handoff_id}.json"
    )
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.parent.mkdir(parents=True, exist_ok=True)

    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    handoff = {
        "handoff_id": handoff_id,
        "lane": "openclaw_like_to_hermes_like",
        "status": "completed",
        "handoff_type": "research_review",
        "from_profile_id": "openclaw_report_exec",
        "to_profile_id": "hermes_research_curator",
        "entity_type": "us_signal_snapshot",
        "entity_id": "2026-04-14",
        "source_entry_id": None,
        "required_action": "interpret_us_signal",
        "inputs": {},
        "expected_outputs": {},
        "history": [
            {
                "status": "completed",
                "at": now_text,
                "by": "validate_model_shadow_openai_preflight.py",
                "note": "synthetic preflight handoff",
            }
        ],
        "created_at": now_text,
        "updated_at": now_text,
    }
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    packet = {
        "packet_id": handoff_id,
        "generated_at": now_text,
        "handoff": {
            "handoff_id": handoff_id,
            "status": "completed",
            "handoff_type": "research_review",
            "entity_type": "us_signal_snapshot",
            "entity_id": "2026-04-14",
            "from_profile_id": "openclaw_report_exec",
            "to_profile_id": "hermes_research_curator",
            "required_action": "interpret_us_signal",
        },
        "source_entry": {
            "id": "registry_preflight",
            "status": "significant",
            "source": "validate_model_shadow_openai_preflight.py",
            "created_at": now_text,
            "snapshot_index": 1,
        },
        "model_route": {
            "global_mode": "disabled",
            "route_global_mode": "disabled",
            "route_status": "configured",
            "entity_type": "us_signal_snapshot",
            "to_profile_id": "hermes_research_curator",
            "task_kind": "us_signal_interpreter",
            "model_slot": "reasoning_batch",
            "packet_mode": "shadow",
            "requires_human_review": True,
            "auto_apply": False,
            "output_contract": "research_context_note_candidate",
            "prompt_pack_rel_path": "12_smr_agents/prompt_packs/hermes_research_curator.md",
            "provider": "openai",
            "model": "gpt-5.4-mini",
            "reasoning_effort": "low",
            "provider_readiness": {
                "provider": "openai",
                "enabled": False,
                "api_key_env": "OPENAI_API_KEY",
                "base_url_env": "OPENAI_BASE_URL",
                "organization_env": "OPENAI_ORGANIZATION",
                "project_env": "OPENAI_PROJECT",
                "has_api_key": False,
                "has_base_url": False,
                "api_style": "responses",
            },
        },
        "source_documents": [
            {
                "rel_path": "06_research/us_signals/2026-04-14-synthetic.md",
                "exists": False,
                "preview": "NVDA earnings beat with strong guide; A股算力链需要重新评估映射强度。",
            }
        ],
    }
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return handoff_id, packet_path


def latest_shadow_entry(db_path, handoff_id):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        """
        SELECT status, payload_json
        FROM task_registry_entry
        WHERE entity_type='model_shadow_execution' AND entity_id=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (handoff_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None, {}
    return row[0], json.loads(row[1] or "{}")


def relative_to_display(path, base_root):
    try:
        return str(path.relative_to(base_root))
    except Exception:
        return str(path)


def main():
    with tempfile.TemporaryDirectory(prefix="smr-shadow-openai-preflight-") as tmp:
        sandbox_root = Path(tmp) / "smr"
        prepare_sandbox_root(sandbox_root)
        configure_shadow_runtime(sandbox_root)
        handoff_id, packet_path = write_preflight_assets(sandbox_root)

        env = os.environ.copy()
        env["SMR_ROOT"] = str(sandbox_root)
        env["SMR_DISABLE_CODEX_OPENAI_FALLBACK"] = "1"
        env.pop("OPENAI_API_KEY", None)

        rc, out, err = run(
            [
                "python3",
                str(MODEL_SHADOW_SCRIPT),
                "--packet-rel-path",
                relative_to_display(packet_path, sandbox_root),
            ],
            env,
        )

        response_json_path = (
            sandbox_root
            / "12_smr_agents"
            / "workspaces"
            / "hermes_research_curator"
            / "shadow_runs"
            / f"{handoff_id}__response.json"
        )
        response_text_path = (
            sandbox_root
            / "12_smr_agents"
            / "workspaces"
            / "hermes_research_curator"
            / "shadow_runs"
            / f"{handoff_id}__response_text.md"
        )
        result_path = (
            sandbox_root
            / "12_smr_agents"
            / "workspaces"
            / "hermes_research_curator"
            / "shadow_runs"
            / f"{handoff_id}__result.md"
        )

        response_payload = json.loads(response_json_path.read_text(encoding="utf-8")) if response_json_path.exists() else {}
        registry_status, registry_payload = latest_shadow_entry(sandbox_root / "01_data" / "db" / "smr.db", handoff_id)

        checks = [
            ("run_model_shadow_runs", rc == 0, out or err),
            (
                "response_json_generated",
                response_json_path.exists(),
                relative_to_display(response_json_path, sandbox_root),
            ),
            (
                "response_text_generated",
                response_text_path.exists(),
                relative_to_display(response_text_path, sandbox_root),
            ),
            (
                "result_md_generated",
                result_path.exists(),
                relative_to_display(result_path, sandbox_root),
            ),
            (
                "execution_status_blocked_missing_api_key",
                response_payload.get("execution_status") == "blocked_missing_api_key",
                json.dumps(
                    {
                        "gate_status": response_payload.get("gate_status"),
                        "execution_status": response_payload.get("execution_status"),
                        "attempted_call": response_payload.get("attempted_call"),
                    },
                    ensure_ascii=False,
                ),
            ),
            (
                "runtime_route_refreshed",
                bool(response_payload.get("route_drift")),
                json.dumps(response_payload.get("route_drift") or {}, ensure_ascii=False),
            ),
            (
                "registry_status_blocked_missing_api_key",
                registry_status == "blocked_missing_api_key",
                json.dumps(
                    {
                        "status": registry_status,
                        "gate_status": registry_payload.get("gate_status"),
                        "attempted_call": registry_payload.get("attempted_call"),
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

        print("SMR model shadow OpenAI preflight validation")
        print(f"- sandbox_root: {sandbox_root}")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"- {name}: {status}")
            print(f"  {detail}")

        if not all(ok for _, ok, _ in checks):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
