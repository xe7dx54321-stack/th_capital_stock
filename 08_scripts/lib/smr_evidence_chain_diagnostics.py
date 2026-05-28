#!/usr/bin/env python3
"""Phase 36 diagnostics for zero-count evidence chains."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates
from smr_ir_source_inventory import build_ir_source_inventory
from smr_phase27_semantic_pipeline import build_semantic_pipeline_for_ticker
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_quality_scoring import build_variable_coverage_matrix
from smr_real_ir_source_connector import discover_real_ir_sources
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, guard_semantic_evidence_candidates
from smr_text_cache import read_text_cache, summarize_text_cache
from smr_wiki import now_ts


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def _table_count(conn: sqlite3.Connection, name: str, ticker: str | None = None) -> int:
    if not _table_exists(conn, name):
        return 0
    try:
        if ticker:
            cols = {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}
            if "ticker" in cols:
                return int(conn.execute(f"SELECT COUNT(*) FROM {name} WHERE ticker=?", (ticker,)).fetchone()[0])
        return int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
    except sqlite3.Error:
        return 0


def _check(name: str, status: str, count: int = 0, **extra: Any) -> dict[str, Any]:
    return {"check": name, "status": status, "count": count, **extra}


def _status_from_count(count: int) -> str:
    return "pass" if count > 0 else "missing"


def _text_cache_hits(sources: list[dict[str, Any]]) -> int:
    hits = 0
    for source in sources:
        if read_text_cache(str(source.get("source_id") or ""), source.get("source_url")):
            hits += 1
    return hits


def build_evidence_chain_zero_diagnostics(conn: sqlite3.Connection, ticker: str = "300394.SZ") -> dict[str, Any]:
    ticker = str(ticker or "300394.SZ").strip().upper()
    evidence_chain = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    real_sources = discover_real_ir_sources(conn, ticker)
    inventory = build_ir_source_inventory(ticker, conn=conn, use_real_sources=True, allow_mock_fallback=False)
    source_inventory = inventory.get("source_inventory") or {}
    sources = source_inventory.get("sources") or real_sources
    pipeline = build_semantic_pipeline_for_ticker(
        ticker,
        conn=conn,
        use_real_sources=True,
        allow_mock_fallback=False,
        use_text_cache=True,
        extract_text_if_missing=False,
        mode="mock",
    )
    candidate_payload = build_semantic_evidence_candidates(
        conn,
        ticker,
        use_real_sources=True,
        allow_mock_fallback=False,
        use_text_cache=True,
        extract_text_if_missing=False,
        mode="mock",
    )
    candidate_rows = flatten_candidates(candidate_payload)
    guarded = guard_semantic_evidence_candidates(candidate_rows, reject_noisy=True) if candidate_rows else {
        "eligible_candidates": [],
        "rejected_candidates": [],
        "review_required_candidates": [],
    }
    persisted = list_semantic_evidence_candidates(conn, ticker=ticker)
    lifecycle = list_lifecycle_states(conn, ticker=ticker)
    matrix = build_variable_coverage_matrix(conn, ticker).get("variable_matrix") or []
    text_hits = _text_cache_hits(sources)
    cache_summary = summarize_text_cache()
    checks = [
        _check("source_inventory", _status_from_count(int(source_inventory.get("sources_found") or 0)), int(source_inventory.get("sources_found") or 0)),
        _check("real_ir_source", _status_from_count(len(real_sources)), len(real_sources)),
        _check("text_cache", _status_from_count(text_hits), text_hits, cache_entries=(cache_summary or {}).get("cache_entries")),
        _check("chunks", _status_from_count(len(pipeline.get("chunks") or [])), len(pipeline.get("chunks") or [])),
        _check("semantic_extraction", _status_from_count(len(pipeline.get("semantic_extractions") or [])), len(pipeline.get("semantic_extractions") or [])),
        _check("semantic_candidates_created", _status_from_count(len(candidate_rows)), len(candidate_rows)),
        _check("quality_filter_eligible", _status_from_count(len(guarded.get("eligible_candidates") or [])), len(guarded.get("eligible_candidates") or [])),
        _check("quality_or_noise_rejected", "observed" if guarded.get("rejected_candidates") else "none", len(guarded.get("rejected_candidates") or [])),
        _check("persistence_guard", _status_from_count(len(guarded.get("eligible_candidates") or [])), len(guarded.get("eligible_candidates") or [])),
        _check("persisted_evidence", _status_from_count(len(persisted)), len(persisted)),
        _check("lifecycle_state", _status_from_count(len(lifecycle)), len(lifecycle)),
        _check("variable_pack_readable", _status_from_count(len(matrix)), len(matrix)),
        _check("ticker_mapping", "pass" if all((source.get("ticker") == ticker) for source in sources) else "needs_review", len(sources)),
        _check(
            "local_db_state",
            "partial" if any(_table_exists(conn, table) for table in ("real_ir_sources", "semantic_evidence_candidates", "evidence_lifecycle_state")) else "missing",
            sum(_table_count(conn, table, ticker) for table in ("real_ir_sources", "semantic_evidence_candidates", "evidence_lifecycle_state")),
            tables={
                "real_ir_sources": _table_count(conn, "real_ir_sources", ticker),
                "semantic_evidence_candidates": _table_count(conn, "semantic_evidence_candidates", ticker),
                "evidence_lifecycle_state": _table_count(conn, "evidence_lifecycle_state", ticker),
            },
        ),
    ]
    root_causes: list[str] = []
    if not persisted:
        root_causes.append("semantic evidence not persisted for 300394.SZ")
    if text_hits == 0:
        root_causes.append("text cache unavailable in current environment")
    if not candidate_rows:
        root_causes.append("semantic extraction or candidate creation not run from usable real text")
    if not real_sources:
        root_causes.append("real IR source inventory missing in local DB")
    if _table_count(conn, "semantic_evidence_candidates", ticker) == 0:
        root_causes.append("local DB state missing or ignored for semantic candidates")
    repair_tasks = [
        {
            "task_type": "REPAIR_EVIDENCE_CHAIN",
            "priority": "high",
            "action": "rerun real IR source inventory, text extraction dry-run, and semantic persistence dry-run for 300394.SZ",
            "expected_result": "semantic evidence candidates become visible before any deeper research conclusion",
        },
        {
            "task_type": "REPAIR_EVIDENCE_CHAIN",
            "priority": "medium",
            "action": "check ignored text cache and DB state before assuming source absence",
            "expected_result": "distinguish local state issue from true source unavailability",
        },
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "evidence_chain_zero_diagnostics": {
            "evidence_chain_count": evidence_chain.get("total_evidence", 0),
            "diagnostic_status": "needs_repair" if int(evidence_chain.get("total_evidence") or 0) == 0 else "evidence_chain_available",
            "checks": checks,
            "likely_root_causes": list(dict.fromkeys(root_causes)) or ["evidence chain is available; zero-chain repair not required"],
            "recommended_repair_tasks": repair_tasks,
        },
        "safety": {
            "diagnostic_only": True,
            "fake_evidence_written": False,
            "repair_executed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def build_evidence_repair_plan(conn: sqlite3.Connection, ticker: str = "300394.SZ") -> dict[str, Any]:
    diagnostics = build_evidence_chain_zero_diagnostics(conn, ticker)
    return {
        "generated_at": now_ts(),
        "ticker": diagnostics.get("ticker"),
        "evidence_repair_plan": {
            "repair_goal": "restore usable evidence chain before deeper research",
            "diagnostic_status": (diagnostics.get("evidence_chain_zero_diagnostics") or {}).get("diagnostic_status"),
            "likely_root_causes": (diagnostics.get("evidence_chain_zero_diagnostics") or {}).get("likely_root_causes") or [],
            "recommended_steps": [
                {
                    "step": 1,
                    "task": "rerun real IR source inventory",
                    "command_hint": "python 08_scripts/reporting/build_phase28_ir_source_inventory.py --tickers 300394.SZ --json",
                    "expected_result": "real sources found or explicit source_missing reason",
                },
                {
                    "step": 2,
                    "task": "rerun text extraction dry-run",
                    "command_hint": "python 08_scripts/jobs/extract_real_ir_document_text.py --tickers 300394.SZ --dry-run --json",
                    "expected_result": "text_extracted > 0 or clear extraction status per source",
                },
                {
                    "step": 3,
                    "task": "rerun semantic extraction from text cache in dry-run",
                    "command_hint": "python 08_scripts/jobs/build_semantic_ir_evidence.py --tickers 300394.SZ --real-sources --use-text-cache --mock --json",
                    "expected_result": "semantic_extractions > 0 with source_url preserved",
                },
                {
                    "step": 4,
                    "task": "rerun semantic candidate persistence dry-run",
                    "command_hint": "python 08_scripts/jobs/persist_semantic_evidence_candidates.py --tickers 300394.SZ --use-text-cache --dry-run --json",
                    "expected_result": "eligible semantic evidence candidates identified without writing raw content",
                },
                {
                    "step": 5,
                    "task": "review dry-run output before any manual execute decision",
                    "command_hint": "python 08_scripts/reporting/build_phase35_evidence_chain_packet.py --ticker 300394.SZ --json",
                    "expected_result": "evidence_chain remains 0 until a separately approved execute step writes candidates",
                },
            ],
            "do_not_do": [
                "do not fabricate evidence",
                "do not manually mark missing evidence as confirmed",
                "do not create pending",
                "do not write raw PDF, HTML, cache, DB, or log artifacts to git",
            ],
        },
        "safety": {
            "plan_only": True,
            "repair_executed": False,
            "fake_evidence_written": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }
