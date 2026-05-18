#!/usr/bin/env python3
"""Sandbox validation for the significant risk-alert -> dual-agent -> dispatch chain."""

import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "01_data/db/smr.db"
RISK_SCRIPT = ROOT / "08_scripts/risk_engine/monitor.py"
CONTROL_LOOP_SCRIPT = ROOT / "08_scripts/agents/run_agent_control_loop.py"
MODEL_PACKET_SCRIPT = ROOT / "08_scripts/agents/build_model_task_packet.py"
MODEL_SHADOW_SCRIPT = ROOT / "08_scripts/agents/run_model_shadow.py"


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
    copy_file(ROOT, tmp_root, Path("00_control/portfolio_policy.json"))
    copy_file(ROOT, tmp_root, Path("00_control/watchlist_registry.md"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/profiles"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/model_runtime"))
    copy_tree(ROOT, tmp_root, Path("12_smr_agents/prompt_packs"))


def reset_sandbox_db(db_path, target_date):
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM position")
    conn.execute("DELETE FROM risk_alert")
    conn.execute("DELETE FROM task_registry_entry")

    latest_price = conn.execute(
        """
        SELECT close
        FROM daily_bar
        WHERE ts_code='300308.SZ'
        ORDER BY trade_date DESC
        LIMIT 1
        """
    ).fetchone()
    if not latest_price:
        conn.close()
        raise SystemExit("Missing latest price for 300308.SZ in sandbox database")

    current_price = float(latest_price[0])
    entry_price = 950.0
    shares = 700
    cost = round(entry_price * shares, 2)
    pnl = round(current_price * shares - cost, 2)
    pnl_pct = round((current_price - entry_price) / entry_price, 4)

    conn.execute(
        """
        INSERT INTO position
        (ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, pnl, pnl_pct, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """,
        ("300308.SZ", target_date, entry_price, shares, cost, None, None, "", pnl, pnl_pct),
    )
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


def main():
    target_date = datetime.now().strftime("%Y-%m-%d")

    with tempfile.TemporaryDirectory(prefix="smr-risk-chain-") as tmp:
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

        reset_sandbox_db(sandbox_db, target_date)

        env = os.environ.copy()
        env["SMR_ROOT"] = str(sandbox_root)
        env["SMR_ALERT_DIR"] = str(sandbox_root / "05_risk" / "alerts")

        checks = []

        rc, out, err = run(["python3", str(RISK_SCRIPT)], env)
        checks.append(("risk_monitor_runs", rc == 0, out or err))

        conn = sqlite3.connect(sandbox_db)
        alert_types = {row[0] for row in conn.execute("SELECT DISTINCT alert_type FROM risk_alert").fetchall()}
        alert_count = conn.execute("SELECT COUNT(*) FROM risk_alert").fetchone()[0]
        conn.close()
        expected_types = {
            "position_limit",
            "sector_concentration",
            "drawdown",
            "weekly_loss",
            "thesis_missing",
            "stop_missing",
            "target_missing",
        }
        checks.append(
            (
                "risk_alert_types_expected",
                expected_types.issubset(alert_types) and alert_count >= len(expected_types),
                f"count={alert_count}; alert_types={','.join(sorted(alert_types))}",
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

        risk_handoff = latest_handoff(handoff_dir, "risk_monitor_snapshot", "hermes_risk_curator")
        checks.append(
            (
                "risk_handoff_completed",
                bool(risk_handoff and risk_handoff.get("status") == "completed"),
                risk_handoff["handoff_id"] if risk_handoff else "missing",
            )
        )

        reporting_handoff = latest_handoff(handoff_dir, "risk_update_candidate", "hermes_reporting_editor")
        checks.append(
            (
                "reporting_handoff_completed",
                bool(reporting_handoff and reporting_handoff.get("status") == "completed"),
                reporting_handoff["handoff_id"] if reporting_handoff else "missing",
            )
        )

        payload = latest_registry_payload(sandbox_db, "risk_monitor_snapshot", target_date)
        checks.append(
            (
                "risk_snapshot_payload_has_alerts",
                (payload.get("alert_count") or 0) > 0,
                json.dumps(payload.get("counts_by_type") or {}, ensure_ascii=False),
            )
        )

        packet_text = dispatch_packet.read_text(encoding="utf-8") if dispatch_packet.exists() else ""
        checks.append(
            (
                "dispatch_packet_contains_risk_sync",
                "风险上下文同步（risk_monitor_snapshot）" in packet_text,
                relative_to_display(dispatch_packet, sandbox_root),
            )
        )

        board_text = dispatch_board.read_text(encoding="utf-8") if dispatch_board.exists() else ""
        checks.append(
            (
                "dispatch_board_contains_alert_context",
                "风险上下文同步（risk_monitor_snapshot）" in board_text and "alert_count: `7`" in board_text,
                relative_to_display(dispatch_board, sandbox_root),
            )
        )

        model_packet_path = None
        shadow_result_path = None
        shadow_response_json_path = None
        shadow_response_text_path = None
        if risk_handoff:
            rc, out, err = run(
                [
                    "python3",
                    str(MODEL_PACKET_SCRIPT),
                    "--handoff-id",
                    risk_handoff["handoff_id"],
                ],
                env,
            )
            model_packet_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_risk_curator"
                / "model_packets"
                / f"{risk_handoff['handoff_id']}.md"
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
                    risk_handoff["handoff_id"],
                ],
                env,
            )
            shadow_result_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_risk_curator"
                / "shadow_runs"
                / f"{risk_handoff['handoff_id']}__result.md"
            )
            shadow_response_json_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_risk_curator"
                / "shadow_runs"
                / f"{risk_handoff['handoff_id']}__response.json"
            )
            shadow_response_text_path = (
                sandbox_root
                / "12_smr_agents"
                / "workspaces"
                / "hermes_risk_curator"
                / "shadow_runs"
                / f"{risk_handoff['handoff_id']}__response_text.md"
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

        print("SMR risk alert significant-branch sandbox validation")
        print(f"- sandbox_root: {sandbox_root}")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"- {name}: {status}")
            print(f"  {detail}")

        if not all(ok for _, ok, _ in checks):
            raise SystemExit(1)


def relative_to_display(path, base_root):
    try:
        return str(path.relative_to(base_root))
    except Exception:
        return str(path)


if __name__ == "__main__":
    main()
