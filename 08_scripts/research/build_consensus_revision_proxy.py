#!/usr/bin/env python3
"""Build internal consensus-revision proxy rows from recent report snapshots."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_consensus_proxy import build_consensus_revision_proxy
from smr_decision import parse_primary_ticker
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "build_consensus_revision_proxy.py"


def load_json(raw: str | None) -> dict:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build internal consensus proxy from investment reports")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT entity_id, payload_json
        FROM task_registry_entry
        WHERE entity_type='investment_report_snapshot'
        ORDER BY datetime(created_at) DESC
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()
    proxies = []
    try:
        for entity_id, raw_payload in rows:
            payload = load_json(raw_payload)
            summary = payload.get("dashboard_summary") or {}
            text = "\n".join(str(summary.get(key) or "") for key in ("action_detail", "confidence_rationale", "primary_signal"))
            ticker, _market = parse_primary_ticker(text)
            entity_ticker, entity_market = parse_primary_ticker(entity_id)
            if not ticker or ("." in str(entity_ticker or "") and "." not in str(ticker or "")):
                ticker, _market = entity_ticker, entity_market
            evidence_ids = []
            for claim in payload.get("claim_evidence_map") or []:
                for evidence in claim.get("evidence") or []:
                    if evidence.get("evidence_id"):
                        evidence_ids.append(evidence["evidence_id"])
            proxy = build_consensus_revision_proxy(conn, text, evidence_ids=evidence_ids[:8], ticker=ticker)
            proxies.append(proxy)
        register_snapshot(
            conn,
            entity_type="consensus_revision_proxy_snapshot",
            entity_id="latest",
            status="success",
            source=SCRIPT_NAME,
            payload={"proxies": proxies},
        )
        conn.commit()
    finally:
        conn.close()
    log_run(SCRIPT_NAME, "success", "consensus revision proxy built", {"proxy_count": len(proxies)})
    print(json.dumps(proxies, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
