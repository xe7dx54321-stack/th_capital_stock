#!/usr/bin/env python3
"""Sandbox validation for the significant us-signal -> dual-agent -> dispatch chain."""

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "01_data" / "db" / "smr.db"
US_SIGNAL_SCRIPT = ROOT / "08_scripts" / "us_signal_harvester" / "earnings_monitor.py"
CONTROL_LOOP_SCRIPT = ROOT / "08_scripts" / "agents" / "run_agent_control_loop.py"
MODEL_PACKET_SCRIPT = ROOT / "08_scripts" / "agents" / "build_model_task_packet.py"
MODEL_SHADOW_SCRIPT = ROOT / "08_scripts" / "agents" / "run_model_shadow.py"


def run(cmd, env, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd or ROOT)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def copy_file(src_root, dst_root, rel_path):
    src = src_root / rel_path
    if not src.exists():
        return
    dst = dst_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src_root, dst_root, rel_path):
    src = src_root / rel_path
    if not src.exists():
        return
    dst = dst_root / rel_path
    shutil.copytree(src, dst, dirs_exist_ok=True)


def prepare_sandbox_root(tmp_root):
    copy_file(ROOT, tmp_root, Path("01_data/db/smr.db"))
    copy_file(ROOT, tmp_root, Path("00_control/dispatch_board.md"))
    copy_file(ROOT, tmp_root, Path("00_control/watchlist_registry.md"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/profiles"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/model_runtime"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/prompt_packs"))


def reset_sandbox_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM us_signal")
    conn.execute("DELETE FROM task_registry_entry")
    conn.commit()
    conn.close()


def load_handoffs(handoff_dir):
    records = []
    for path in sorted(handoff_dir.glob("*.json"), reverse=True):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["path"] = path
        records.append(payload)
    return records


def latest_handoff(handoff_dir, entity_type, to_profile_id=None):
    for record in load_handoffs(handoff_dir):
        if record.get("entity_type") != entity_type:
            continue
        if to_profile_id and record.get("to_profile_id") != to_profile_id:
            continue
        return record
    return None


def latest_registry_payload(db_path, entity_type, entity_id):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entry
        WHERE entity_type=? AND entity_id=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type, entity_id),
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}


def relative_to_display(path, base_root):
    try:
        return str(path.relative_to(base_root))
    except Exception:
        return str(path)


def main():
    target_date = datetime.now().strftime("%Y-%m-%d")

    with tempfile.TemporaryDirectory(prefix="smr-us-signal-chain-") as tmp:
        sandbox_root = Path(tmp) / "smr"
        prepare_sandbox_root(sandbox_root)
        sandbox_db = sandbox_root / "01_data" / "db" / "smr.db"
        handoff_dir = sandbox_root / "12_smr_agents" / "handoffs"
        dispatch_packet = (
            sandbox_root
            / "12_smr_agents"
            / "workspaces"
            / "hermes_reporting_editor"
            / "dispatch_packets"
            / f"{target_date}__dispatch_packet_candidate.md"
        )
        dispatch_board = sandbox_root / "00_control" / "dispatch_board.md"

        reset_sandbox_db(sandbox_db)

        env = os.environ.copy()
        env["SMR_ROOT"] = str(sandbox_root)

        checks = []

        rc, out, err = run(["python3", str(US_SIGNAL_SCRIPT)], env)
        checks.append(("us_signal_script_runs", rc == 0, out or err))

        conn = sqlite3.connect(sandbox_db)
        us_signal_count = conn.execute("SELECT COUNT(*) FROM us_signal").fetchone()[0]
        saved_symbols = [row[0] for row in conn.execute("SELECT DISTINCT symbol FROM us_signal ORDER BY symbol").fetchall()]
        conn.close()
        checks.append(
            (
                "us_signal_rows_saved",
                us_signal_count > 0,
                f"count={us_signal_count}; symbols={','.join(saved_symbols[:12])}",
            )
        )

        rc, out, err = run(
            [
                "python3",
                str(CONTROL_LOOP_SCRIPT),
                "--date",
                target_date,
                "--build-dispatch",
                "--apply-dispatch",
                "--research-governance-mode",
                "skip",
            ],
            env,
        )
        checks.append(("agent_control_loop_runs", rc == 0, out or err))

        research_handoff = latest_handoff(handoff_dir, "us_signal_snapshot", "hermes_research_curator")
        checks.append(
            (
                "research_handoff_completed",
                bool(research_handoff and research_handoff.get("status") == "completed"),
                research_handoff["handoff_id"] if research_handoff else "missing",
            )
        )

        reporting_handoff = latest_handoff(handoff_dir, "research_context_note", "hermes_reporting_editor")
        checks.append(
            (
                "reporting_handoff_completed",
                bool(reporting_handoff and reporting_handoff.get("status") == "completed"),
                reporting_handoff["handoff_id"] if reporting_handoff else "missing",
            )
        )

        payload = latest_registry_payload(sandbox_db, "us_signal_snapshot", target_date)
        checks.append(
            (
                "us_signal_snapshot_has_saved_count",
                (payload.get("saved_count") or 0) > 0,
                json.dumps(
                    {
                        "saved_count": payload.get("saved_count"),
                        "symbols": payload.get("symbols"),
                        "signal_types": payload.get("signal_types"),
                    },
                    ensure_ascii=False,
                ),
            )
        )

        packet_text = dispatch_packet.read_text(encoding="utf-8") if dispatch_packet.exists() else ""
        checks.append(
            (
                "dispatch_packet_contains_us_signal_sync",
                "研究上下文同步（us_signal_snapshot）" in packet_text,
                relative_to_display(dispatch_packet, sandbox_root),
            )
        )

        board_text = dispatch_board.read_text(encoding="utf-8") if dispatch_board.exists() else ""
        checks.append(
            (
                "dispatch_board_contains_us_signal_sync",
                "研究上下文同步（us_signal_snapshot）" in board_text,
                relative_to_display(dispatch_board, sandbox_root),
            )
        )

        model_packet_path = None
        shadow_result_path = None
        shadow_response_json_path = None
        shadow_response_text_path = None
        if research_handoff:
            rc, out, err = run(
                [
                    "python3",
                    str(MODEL_PACKET_SCRIPT),
                    "--handoff-id",
                    research_handoff["handoff_id"],
                ],
                env,
            )
            model_packet_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_research_curator"
                / "model_packets"
                / f"{research_handoff['handoff_id']}.md"
            )
            checks.append(("model_task_packet_runs", rc == 0, out or err))
            checks.append(
                (
                    "model_task_packet_generated",
                    bool(model_packet_path.exists()),
                    relative_to_display(model_packet_path, sandbox_root),
                )
            )
            rc, out, err = run(
                [
                    "python3",
                    str(MODEL_SHADOW_SCRIPT),
                    "--handoff-id",
                    research_handoff["handoff_id"],
                ],
                env,
            )
            shadow_result_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_research_curator"
                / "shadow_runs"
                / f"{research_handoff['handoff_id']}__result.md"
            )
            shadow_response_json_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_research_curator"
                / "shadow_runs"
                / f"{research_handoff['handoff_id']}__response.json"
            )
            shadow_response_text_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_research_curator"
                / "shadow_runs"
                / f"{research_handoff['handoff_id']}__response_text.md"
            )
            checks.append(("model_shadow_runs", rc == 0, out or err))
            checks.append(
                (
                    "model_shadow_generated",
                    bool(shadow_result_path.exists()),
                    relative_to_display(shadow_result_path, sandbox_root),
                )
            )
            checks.append(
                (
                    "model_shadow_response_json_generated",
                    bool(shadow_response_json_path.exists()),
                    relative_to_display(shadow_response_json_path, sandbox_root),
                )
            )
            checks.append(
                (
                    "model_shadow_response_text_generated",
                    bool(shadow_response_text_path.exists()),
                    relative_to_display(shadow_response_text_path, sandbox_root),
                )
            )

        print("SMR us-signal significant-branch sandbox validation")
        print(f"- sandbox_root: {sandbox_root}")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"- {name}: {status}")
            print(f"  {detail}")

        if not all(ok for _, ok, _ in checks):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
