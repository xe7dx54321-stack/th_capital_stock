#!/usr/bin/env python3
"""Phase 8 repeated blocker triage and repair-queue builder."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_blocker_repair_queue import ensure_blocker_repair_queue_tables, list_repair_tasks, upsert_repair_task
from smr_blocker_taxonomy import normalize_blockers, priority_for_blocker
from smr_live_run_history import ensure_live_run_history_tables, list_live_run_history
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase8_blocker_triage.py"


def market_for_ticker(ticker: str | None) -> str:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    return "US"


def _ticker_status_from_run(run: dict[str, Any], ticker: str) -> dict[str, Any]:
    per_ticker = run.get("per_ticker_status") or {}
    return per_ticker.get(ticker) or per_ticker.get(ticker.upper()) or {}


def _blockers_for_run_ticker(run: dict[str, Any], ticker: str) -> list[dict[str, Any]]:
    direct = (run.get("blocking_factors") or {}).get(ticker) or (run.get("blocking_factors") or {}).get(ticker.upper()) or []
    if not direct:
        direct = (_ticker_status_from_run(run, ticker).get("blocking_factors") or [])
    status = _ticker_status_from_run(run, ticker)
    return normalize_blockers(
        direct,
        context={
            "proxy_quality": status.get("proxy_quality"),
            "fundamentals_missing_fields": status.get("fundamentals_missing_fields") or status.get("missing_fields") or [],
        },
    )


def aggregate_blockers(runs: list[dict[str, Any]], watchlist_id: str | None = None) -> dict[str, Any]:
    blocker_counter: Counter[str] = Counter()
    blocker_tickers: dict[str, set[str]] = defaultdict(set)
    blocker_markets: dict[str, set[str]] = defaultdict(set)
    blocker_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ticker_summary: dict[str, dict[str, Any]] = {}
    source_run_ids_by_ticker_code: dict[tuple[str, str], list[str]] = defaultdict(list)
    affected_fields_by_ticker_code: dict[tuple[str, str], set[str]] = defaultdict(set)

    for run in runs:
        run_id = str(run.get("run_id") or "")
        tickers = set((run.get("blocking_factors") or {}).keys()) | set((run.get("per_ticker_status") or {}).keys())
        for ticker in sorted(tickers):
            ticker = str(ticker or "").upper()
            status = _ticker_status_from_run(run, ticker)
            blockers = _blockers_for_run_ticker(run, ticker)
            if not blockers:
                continue
            ticker_entry = ticker_summary.setdefault(
                ticker,
                {
                    "market": market_for_ticker(ticker),
                    "current_status": status.get("status") or "unknown",
                    "current_action": status.get("action"),
                    "repeated_blockers": [],
                    "minimum_fix_path": [],
                    "source_run_ids": [],
                },
            )
            if status.get("status"):
                ticker_entry["current_status"] = status.get("status")
            if run_id:
                ticker_entry["source_run_ids"] = list(dict.fromkeys([*ticker_entry["source_run_ids"], run_id]))
            for blocker in blockers:
                code = blocker["code"]
                blocker_counter[code] += 1
                blocker_tickers[code].add(ticker)
                blocker_markets[code].add(market_for_ticker(ticker))
                blocker_examples[code].append(blocker)
                source_run_ids_by_ticker_code[(ticker, code)].append(run_id)
                for field in blocker.get("affected_fields") or []:
                    affected_fields_by_ticker_code[(ticker, code)].add(str(field))
                if code not in ticker_entry["repeated_blockers"]:
                    ticker_entry["repeated_blockers"].append(code)
                    ticker_entry["minimum_fix_path"].append(
                        {
                            "code": code,
                            "fix": blocker.get("suggested_fix"),
                        }
                    )

    top_blockers = []
    for rank, (code, frequency) in enumerate(blocker_counter.most_common(), start=1):
        example = blocker_examples[code][0]
        top_blockers.append(
            {
                "rank": rank,
                "blocker_code": code,
                "blocker_type": example.get("type"),
                "frequency": frequency,
                "affected_tickers": sorted(blocker_tickers[code]),
                "markets": sorted(blocker_markets[code]),
                "severity": example.get("severity"),
                "fixability": example.get("fixability"),
                "expected_impact": example.get("expected_impact"),
                "suggested_fix": example.get("suggested_fix"),
                "priority": priority_for_blocker(example),
            }
        )

    most_common = top_blockers[0] if top_blockers else {}
    return {
        "summary_status": "ok",
        "generated_at": now_ts(),
        "run_count": len(runs),
        "watchlist_id": watchlist_id or (runs[0].get("watchlist_id") if runs else None),
        "most_common_blocker": most_common.get("blocker_code"),
        "most_affected_market": (most_common.get("markets") or [None])[0],
        "highest_priority_repair": most_common.get("suggested_fix"),
        "top_repeated_blockers": top_blockers,
        "ticker_blocker_summary": ticker_summary,
        "source_run_ids_by_ticker_code": {
            f"{ticker}|{code}": list(dict.fromkeys(run_ids))
            for (ticker, code), run_ids in source_run_ids_by_ticker_code.items()
        },
        "affected_fields_by_ticker_code": {
            f"{ticker}|{code}": sorted(fields)
            for (ticker, code), fields in affected_fields_by_ticker_code.items()
        },
    }


def upsert_queue_from_triage(conn: sqlite3.Connection, triage: dict[str, Any]) -> list[dict[str, Any]]:
    ensure_blocker_repair_queue_tables(conn)
    created: list[dict[str, Any]] = []
    source_runs = triage.get("source_run_ids_by_ticker_code") or {}
    affected_fields = triage.get("affected_fields_by_ticker_code") or {}
    blocker_lookup = {item["blocker_code"]: item for item in triage.get("top_repeated_blockers") or []}
    for ticker, summary in (triage.get("ticker_blocker_summary") or {}).items():
        market = summary.get("market") or market_for_ticker(ticker)
        for code in summary.get("repeated_blockers") or []:
            blocker = blocker_lookup.get(code) or {"blocker_code": code}
            key = f"{ticker}|{code}"
            task = upsert_repair_task(
                conn,
                ticker=ticker,
                market=market,
                watchlist_id=triage.get("watchlist_id"),
                blocker_code=code,
                blocker_type=blocker.get("blocker_type"),
                priority=blocker.get("priority"),
                severity=blocker.get("severity"),
                fixability=blocker.get("fixability"),
                expected_impact=blocker.get("expected_impact"),
                suggested_fix=blocker.get("suggested_fix"),
                source_run_ids=source_runs.get(key) or summary.get("source_run_ids") or [],
                affected_fields=affected_fields.get(key) or [],
                metadata={
                    "source": SCRIPT_NAME,
                    "frequency": blocker.get("frequency"),
                    "current_status": summary.get("current_status"),
                    "minimum_fix_path": summary.get("minimum_fix_path") or [],
                },
            )
            created.append(task)
    return created


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 8 Blocker Triage",
        "",
        "## Overall",
        "",
        f"- Run count: `{payload.get('run_count')}`",
        f"- Watchlist: `{payload.get('watchlist_id')}`",
        f"- Most common blocker: `{payload.get('most_common_blocker') or '-'}`",
        f"- Most affected market: `{payload.get('most_affected_market') or '-'}`",
        f"- Highest priority repair: {payload.get('highest_priority_repair') or '-'}",
        f"- Repair tasks upserted: `{payload.get('repair_tasks_upserted') or 0}`",
        "",
        "## Top Repeated Blockers",
        "",
        "| Rank | Blocker | Type | Frequency | Affected Tickers | Severity | Fixability | Suggested Fix |",
        "|---:|---|---|---:|---|---|---|---|",
    ]
    for item in payload.get("top_repeated_blockers") or []:
        lines.append(
            "| {rank} | {code} | {typ} | {freq} | {tickers} | {sev} | {fix} | {suggested} |".format(
                rank=item.get("rank"),
                code=item.get("blocker_code"),
                typ=item.get("blocker_type") or "-",
                freq=item.get("frequency") or 0,
                tickers=", ".join(item.get("affected_tickers") or []),
                sev=item.get("severity") or "-",
                fix=item.get("fixability") or "-",
                suggested=item.get("suggested_fix") or "-",
            )
        )
    lines.extend(
        [
            "",
            "## Per Ticker Triage",
            "",
            "| Ticker | Market | Current Status | Repeated Blockers | Minimum Fix Path |",
            "|---|---|---|---|---|",
        ]
    )
    for ticker, item in sorted((payload.get("ticker_blocker_summary") or {}).items()):
        fixes = "; ".join(path.get("fix") or "" for path in item.get("minimum_fix_path") or []) or "-"
        lines.append(
            f"| {ticker} | {item.get('market') or '-'} | {item.get('current_status') or '-'} | {', '.join(item.get('repeated_blockers') or []) or '-'} | {fixes} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 8 repeated blocker triage")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--upsert-repair-queue", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_live_run_history_tables(conn)
        runs = list_live_run_history(conn, watchlist_id=args.watchlist, limit=args.limit)
        payload = aggregate_blockers(runs, watchlist_id=args.watchlist)
        repair_tasks = []
        if args.upsert_repair_queue:
            repair_tasks = upsert_queue_from_triage(conn, payload)
            payload["repair_tasks_upserted"] = len(repair_tasks)
            payload["repair_queue_open_count"] = len(list_repair_tasks(conn, status="open", watchlist_id=args.watchlist, limit=500))
        else:
            payload["repair_tasks_upserted"] = 0
        payload["repair_tasks"] = repair_tasks[:20]
        output_dir = project_path("06_reports", "adhoc", "phase8")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_phase8_blocker_triage.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="phase8_blocker_triage",
            entity_id=payload["generated_at"][:10],
            status=payload["summary_status"],
            source=SCRIPT_NAME,
            payload={**payload, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase8 blocker triage built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
