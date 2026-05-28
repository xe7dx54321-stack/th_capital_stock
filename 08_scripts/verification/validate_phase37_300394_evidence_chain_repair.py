#!/usr/bin/env python3
"""Validate Phase 37 300394 evidence-chain repair output."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_phase37_300394_evidence_chain_repair import build_payload as build_repair_payload
from smr_agents import DB_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    payload = build_repair_payload(conn, mode="dry_run")
    body = payload.get("evidence_chain_repair") or {}
    issues = []
    if body.get("repair_status") not in {"partial_repair_dry_run", "controlled_execute_completed"}:
        issues.append("unexpected_repair_status")
    if payload.get("safety", {}).get("fake_evidence_written"):
        issues.append("fake_evidence_written")
    return {
        **payload,
        "validation": {
            "overall_status": "pass" if not issues else "fail",
            "issues": issues,
            "root_cause_present": bool(body.get("root_cause")),
            "new_pending_created": payload.get("safety", {}).get("new_pending_created", 0),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 37 300394 evidence-chain repair")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
