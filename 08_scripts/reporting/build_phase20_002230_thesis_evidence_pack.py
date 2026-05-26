#!/usr/bin/env python3
"""Build Phase 20 evidence-backed thesis candidate pack for 002230.SZ."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase19_thesis_evidence_gate import build_ticker_payload as build_phase19_thesis_gate
from smr_agents import DB_PATH
from smr_evidence_quality import build_evidence_quality_gate
from smr_proxy_signal_gate import build_proxy_signal_gate
from smr_registry import register_snapshot
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase20_002230_thesis_evidence_pack.py"
TARGET_TICKER = "002230.SZ"


def _claim_graph_support(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_claims'").fetchone()
    if not exists:
        return {"status": "missing", "claim_ids": [], "missing": ["claim_graph_support"]}
    rows = conn.execute(
        """
        SELECT claim_id, claim_type, importance, confidence
        FROM research_claims
        WHERE UPPER(COALESCE(ticker, ''))=?
        ORDER BY id DESC
        LIMIT 20
        """,
        (ticker.upper(),),
    ).fetchall()
    claim_ids = [row[0] for row in rows]
    if not rows:
        return {"status": "missing", "claim_ids": [], "missing": ["claim_graph_support", "direct order/demand claim"]}
    has_core = any(row[2] == "core" for row in rows)
    return {
        "status": "partial" if has_core else "weak",
        "claim_ids": claim_ids[:8],
        "missing": [] if has_core else ["direct order/demand claim"],
    }


def _filing_or_news_support(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    gate = build_evidence_quality_gate(conn, ticker)
    evidence = gate.get("evidence") or []
    usable = [item for item in evidence if item.get("quality_level") in {"high", "medium"} and item.get("evidence_id")]
    if usable:
        return {
            "status": "partial",
            "evidence_ids": [item["evidence_id"] for item in usable[:8]],
            "missing": ["recent direct AI infrastructure demand evidence"],
        }
    return {"status": "missing", "evidence_ids": [], "missing": ["filing_or_news_support"]}


def build_payload(conn: sqlite3.Connection, *, include_metadata_simulation: bool = False) -> dict[str, Any]:
    p19 = build_phase19_thesis_gate(conn, TARGET_TICKER)
    proxy = build_proxy_signal_gate(conn, TARGET_TICKER)
    claim_support = _claim_graph_support(conn, TARGET_TICKER)
    filing_support = _filing_or_news_support(conn, TARGET_TICKER)
    metadata_confidence = float((p19.get("after_metadata_simulation") or {}).get("confidence") or 0.0)
    metadata_status = "strong" if metadata_confidence >= 0.75 else ("partial" if metadata_confidence >= 0.5 else "weak")
    has_non_metadata_evidence = claim_support["status"] in {"partial"} or filing_support["status"] in {"partial"}
    candidate_thesis = (p19.get("after_metadata_simulation") or {}).get("candidate_thesis_type") or "unknown"
    thesis_status = "evidence_backed_candidate" if candidate_thesis != "unknown" and has_non_metadata_evidence else "metadata_only_candidate"
    confidence = 0.76 if thesis_status == "evidence_backed_candidate" else min(metadata_confidence, 0.65)
    proxy_gate = proxy.get("proxy_signal_gate") or {}
    allow_pending = False
    next_fix = []
    if claim_support["status"] != "partial":
        next_fix.append("build claim graph from filing/news evidence")
    if proxy_gate.get("status") != "strong":
        next_fix.append("strengthen proxy signal with independent source count >= 2")
    if "recent direct AI infrastructure demand evidence" in filing_support.get("missing", []):
        next_fix.append("extract AI infrastructure demand claim from filings/news")
    return {
        "ticker": TARGET_TICKER,
        "before": p19.get("before") or {"primary_thesis_type": "unknown", "confidence": None, "allow_pending": False},
        "after": {
            "candidate_thesis_type": candidate_thesis,
            "confidence": confidence,
            "thesis_status": thesis_status,
            "allow_pending": allow_pending,
        },
        "after_metadata_simulation": p19.get("after_metadata_simulation") if include_metadata_simulation else None,
        "evidence_pack": {
            "metadata_support": {
                "status": metadata_status,
                "evidence": ["watchlist_metadata_patch"] if metadata_status in {"strong", "partial"} else [],
                "metadata_alone_allows_pending": False,
            },
            "claim_graph_support": claim_support,
            "proxy_signal_support": {
                "status": proxy_gate.get("status") or "missing",
                "missing": proxy_gate.get("missing_requirements") or ["dominant_proxy_signal"],
                "is_official_consensus": False,
            },
            "filing_or_news_support": filing_support,
        },
        "next_fix": next_fix or ["keep thesis candidate under observation until promotion gates pass"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 20 002230 thesis evidence pack")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--include-metadata-simulation", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, include_metadata_simulation=args.include_metadata_simulation)
        register_snapshot(
            conn,
            entity_type="phase20_002230_thesis_evidence_pack",
            entity_id=TARGET_TICKER,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase20 002230 thesis evidence pack built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
