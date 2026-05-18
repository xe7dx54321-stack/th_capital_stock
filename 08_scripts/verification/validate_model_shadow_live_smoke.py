#!/usr/bin/env python3
"""Sandbox smoke validation for live provider-backed SMR model shadow calls."""

import argparse
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


def configure_shadow_runtime(tmp_root, provider_name):
    model_profiles_path = tmp_root / "12_smr_agents" / "model_runtime" / "model_profiles.json"
    task_routes_path = tmp_root / "12_smr_agents" / "model_runtime" / "task_routes.json"

    model_profiles = json.loads(model_profiles_path.read_text(encoding="utf-8"))
    model_profiles["global_mode"] = "shadow"
    for name, provider in (model_profiles.get("providers") or {}).items():
        provider["enabled"] = name == provider_name
    model_profiles_path.write_text(json.dumps(model_profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    task_routes = json.loads(task_routes_path.read_text(encoding="utf-8"))
    task_routes["global_mode"] = "shadow"
    task_routes_path.write_text(json.dumps(task_routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configured_slot_model(tmp_root, slot_name):
    model_profiles_path = tmp_root / "12_smr_agents" / "model_runtime" / "model_profiles.json"
    model_profiles = json.loads(model_profiles_path.read_text(encoding="utf-8"))
    slot = (model_profiles.get("model_slots") or {}).get(slot_name) or {}
    return slot.get("model")


def live_packet(provider_name, tmp_root):
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if provider_name in {"openai", "minimax"}:
        model_slot = "reasoning_batch"
        model = configured_slot_model(tmp_root, model_slot)
        return {
            "handoff_id": f"handoff_{provider_name}_shadow_live_smoke",
            "entity_type": "us_signal_snapshot",
            "entity_id": "2026-04-14",
            "from_profile_id": "openclaw_report_exec",
            "to_profile_id": "hermes_research_curator",
            "required_action": "interpret_us_signal",
            "task_kind": "us_signal_interpreter",
            "model_slot": model_slot,
            "provider": provider_name,
            "model": model or ("gpt-5.4" if provider_name == "openai" else "MiniMax-M2.7"),
            "prompt_pack_rel_path": "12_smr_agents/prompt_packs/hermes_research_curator.md",
            "output_contract": "research_context_note_candidate",
            "preview": "AMD、AVGO 上涨，NOW 下跌，判断这些显著变化对 A/H 链路有没有真正需要跟踪的映射。",
            "now_text": now_text,
        }
    return {
        "handoff_id": "handoff_anthropic_shadow_live_smoke",
        "entity_type": "review_queue",
        "entity_id": "review_queue_live_smoke",
        "from_profile_id": "openclaw_report_exec",
        "to_profile_id": "hermes_research_curator",
        "required_action": "review_queue_triage",
        "task_kind": "governance_triage",
        "model_slot": "review_second_opinion",
        "provider": "anthropic",
        "model": configured_slot_model(tmp_root, "review_second_opinion") or "claude-sonnet-4-6",
        "prompt_pack_rel_path": "12_smr_agents/prompt_packs/hermes_research_curator.md",
        "output_contract": "review_recommendation_only",
        "preview": "有 3 个待审 draft，其中 1 个证据充分，1 个来源老旧，1 个标题党风险高。请给出中文 triage 建议。",
        "now_text": now_text,
    }


def write_smoke_assets(tmp_root, provider_name):
    cfg = live_packet(provider_name, tmp_root)
    handoff_id = cfg["handoff_id"]
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

    handoff = {
        "handoff_id": handoff_id,
        "lane": "openclaw_like_to_hermes_like",
        "status": "completed",
        "handoff_type": "research_review",
        "from_profile_id": cfg["from_profile_id"],
        "to_profile_id": cfg["to_profile_id"],
        "entity_type": cfg["entity_type"],
        "entity_id": cfg["entity_id"],
        "source_entry_id": None,
        "required_action": cfg["required_action"],
        "inputs": {},
        "expected_outputs": {},
        "history": [
            {
                "status": "completed",
                "at": cfg["now_text"],
                "by": "validate_model_shadow_live_smoke.py",
                "note": "synthetic live smoke handoff",
            }
        ],
        "created_at": cfg["now_text"],
        "updated_at": cfg["now_text"],
    }
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    packet = {
        "packet_id": handoff_id,
        "generated_at": cfg["now_text"],
        "handoff": {
            "handoff_id": handoff_id,
            "status": "completed",
            "handoff_type": "research_review",
            "entity_type": cfg["entity_type"],
            "entity_id": cfg["entity_id"],
            "from_profile_id": cfg["from_profile_id"],
            "to_profile_id": cfg["to_profile_id"],
            "required_action": cfg["required_action"],
        },
        "source_entry": {
            "id": f"registry_{provider_name}_live_smoke",
            "status": "significant",
            "source": "validate_model_shadow_live_smoke.py",
            "created_at": cfg["now_text"],
            "snapshot_index": 1,
        },
        "model_route": {
            "global_mode": "disabled",
            "route_global_mode": "disabled",
            "route_status": "configured",
            "entity_type": cfg["entity_type"],
            "to_profile_id": cfg["to_profile_id"],
            "task_kind": cfg["task_kind"],
            "model_slot": cfg["model_slot"],
            "packet_mode": "shadow",
            "requires_human_review": True,
            "auto_apply": False,
            "output_contract": cfg["output_contract"],
            "prompt_pack_rel_path": cfg["prompt_pack_rel_path"],
            "provider": cfg["provider"],
            "model": cfg["model"],
            "reasoning_effort": "medium",
            "provider_readiness": {
                "provider": cfg["provider"],
                "enabled": False,
                "api_key_env": {
                    "openai": "OPENAI_API_KEY",
                    "minimax": "MINIMAX_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                }[provider_name],
                "base_url_env": {
                    "openai": "OPENAI_BASE_URL",
                    "minimax": "MINIMAX_BASE_URL",
                    "anthropic": "ANTHROPIC_BASE_URL",
                }[provider_name],
                "has_api_key": False,
                "has_base_url": False,
                "api_style": {
                    "openai": "responses",
                    "minimax": "anthropic_messages",
                    "anthropic": "messages",
                }[provider_name],
            },
        },
        "source_documents": [
            {
                "rel_path": f"06_research/live_smoke/{provider_name}.md",
                "exists": False,
                "preview": cfg["preview"],
            }
        ],
    }
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return handoff_id, packet_path


def relative_to_display(path, base_root):
    try:
        return str(path.relative_to(base_root))
    except Exception:
        return str(path)


def main():
    parser = argparse.ArgumentParser(description="Live smoke validation for SMR model shadow providers")
    parser.add_argument("--provider", choices=["openai", "anthropic", "minimax"], required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix=f"smr-shadow-{args.provider}-live-") as tmp:
        sandbox_root = Path(tmp) / "smr"
        prepare_sandbox_root(sandbox_root)
        configure_shadow_runtime(sandbox_root, args.provider)
        handoff_id, packet_path = write_smoke_assets(sandbox_root, args.provider)

        env = os.environ.copy()
        env["SMR_ROOT"] = str(sandbox_root)

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

        checks = [
            ("run_model_shadow_runs", rc == 0, out or err),
            ("response_json_generated", response_json_path.exists(), relative_to_display(response_json_path, sandbox_root)),
            ("response_text_generated", response_text_path.exists(), relative_to_display(response_text_path, sandbox_root)),
            ("result_md_generated", result_path.exists(), relative_to_display(result_path, sandbox_root)),
            (
                "execution_status_shadow_call_succeeded",
                response_payload.get("execution_status") == "shadow_call_succeeded",
                json.dumps(
                    {
                        "gate_status": response_payload.get("gate_status"),
                        "execution_status": response_payload.get("execution_status"),
                        "http_status": response_payload.get("http_status"),
                        "error": response_payload.get("error"),
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

        print(f"SMR model shadow {args.provider} live smoke validation")
        print(f"- sandbox_root: {sandbox_root}")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"- {name}: {status}")
            print(f"  {detail}")

        if not all(ok for _, ok, _ in checks):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
