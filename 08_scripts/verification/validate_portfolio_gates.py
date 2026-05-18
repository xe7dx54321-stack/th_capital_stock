#!/usr/bin/env python3
"""Sandbox validation for SMR entry gates and risk engine using a cloned database."""

import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "01_data/db/smr.db"
ENTRY_SCRIPT = ROOT / "08_scripts/portfolio/entry.py"
PNL_SCRIPT = ROOT / "08_scripts/portfolio/pnl.py"
RISK_SCRIPT = ROOT / "08_scripts/risk_engine/monitor.py"


def run(cmd, env):
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    with tempfile.TemporaryDirectory(prefix="smr-verify-") as tmp:
        tmpdir = Path(tmp)
        db_copy = tmpdir / "smr.db"
        alert_dir = tmpdir / "alerts"
        positions_dir = tmpdir / "positions"
        shutil.copy2(DB_PATH, db_copy)

        env = os.environ.copy()
        env["SMR_ROOT"] = str(ROOT)
        env["SMR_DB_PATH"] = str(db_copy)
        env["SMR_ALERT_DIR"] = str(alert_dir)
        env["SMR_POSITIONS_DIR"] = str(positions_dir)

        checks = []

        rc, out, err = run(
            [
                "python3",
                str(ENTRY_SCRIPT),
                "--ts-code",
                "002281.SZ",
                "--entry-price",
                "108.09",
                "--shares",
                "100",
                "--target-price",
                "150",
                "--stop-loss",
                "88",
                "--thesis",
                "sandbox validation recommendation pass",
                "--confirm-recommendation",
                "--dry-run",
            ],
            env,
        )
        checks.append(("recommended_dry_run", rc == 0, out or err))

        rc, out, err = run(
            [
                "python3",
                str(ENTRY_SCRIPT),
                "--ts-code",
                "300394.SZ",
                "--entry-price",
                "346.9",
                "--shares",
                "100",
                "--target-price",
                "420",
                "--stop-loss",
                "300",
                "--thesis",
                "sandbox validation candidate blocked",
                "--confirm-recommendation",
                "--dry-run",
            ],
            env,
        )
        checks.append(("candidate_blocked", rc != 0 and "not currently in the recommended pool" in (out + err), out or err))

        conn = sqlite3.connect(db_copy)
        conn.execute(
            """
            INSERT INTO position
            (ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, status)
            VALUES (?, date('now'), ?, ?, ?, ?, ?, ?, 'open')
            """,
            ("300308.SZ", 900.0, 700, 630000.0, 1000.0, 680.0, "sandbox risk validation position"),
        )
        conn.commit()
        conn.close()

        rc, out, err = run(["python3", str(PNL_SCRIPT)], env)
        checks.append(("pnl_runs", rc == 0, out or err))

        rc, out, err = run(["python3", str(RISK_SCRIPT)], env)
        checks.append(("risk_runs", rc == 0, out or err))

        conn = sqlite3.connect(db_copy)
        alert_types = {row[0] for row in conn.execute("SELECT DISTINCT alert_type FROM risk_alert").fetchall()}
        conn.close()
        expected = {"position_limit", "sector_concentration", "weekly_loss", "drawdown"}
        checks.append(("risk_alerts_expected", expected.issubset(alert_types), ",".join(sorted(alert_types))))

        print("SMR portfolio gate sandbox validation")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"- {name}: {status}")
            print(f"  {detail}")

        if not all(ok for _, ok, _ in checks):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
