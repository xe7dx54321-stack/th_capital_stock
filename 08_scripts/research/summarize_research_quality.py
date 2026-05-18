#!/usr/bin/env python3
"""Summarize latest research quality for current candidate/recommended pool."""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

ROOT = project_path()
DB_PATH = project_path("01_data", "db", "smr.db")
OUTPUT_DIR = project_path("02_research", "summary")


def main():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT
            s.pool_type,
            s.ts_code,
            s.sector,
            s.score,
            d.thesis_strength,
            d.customer_evidence,
            d.order_evidence,
            d.commercialization_evidence,
            d.valuation_risk,
            d.open_gap_count,
            d.research_quality_score,
            d.reason
        FROM stock_pool_current s
        LEFT JOIN research_decision_latest d ON d.ts_code = s.ts_code
        WHERE s.pool_type IN ('candidate', 'recommended')
        ORDER BY
            CASE s.pool_type WHEN 'recommended' THEN 1 ELSE 2 END,
            COALESCE(d.research_quality_score, s.score, 0) DESC,
            s.ts_code
        """
    ).fetchall()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"{today}_research_quality_snapshot.md"

    lines = [
        "# SMR 研究质量快照",
        "",
        f"- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- source: stock_pool_current + research_decision_latest",
        "",
        "| pool_type | ts_code | sector | thesis_strength | customer | order | commercialization | valuation_risk | gaps | research_quality_score | pool_score |",
        "|-----------|---------|--------|-----------------|----------|-------|-------------------|----------------|------|------------------------|-----------|",
    ]
    for row in rows:
        pool_type, ts_code, sector, score, thesis_strength, customer, order_evidence, commercialization, valuation_risk, gaps, quality_score, reason = row
        lines.append(
            f"| {pool_type} | {ts_code} | {sector or ''} | {thesis_strength or '-'} | {customer or '-'} | {order_evidence or '-'} | {commercialization or '-'} | {valuation_risk or '-'} | {gaps if gaps is not None else '-'} | {quality_score if quality_score is not None else '-'} | {score if score is not None else '-'} |"
        )

    lines.extend(["", "## Notes", ""])
    for row in rows:
        pool_type, ts_code, sector, score, thesis_strength, customer, order_evidence, commercialization, valuation_risk, gaps, quality_score, reason = row
        lines.append(f"- `{ts_code}` `{pool_type}`: {reason or 'no reason'}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    counts_by_pool = {}
    for row in rows:
        counts_by_pool[row[0]] = counts_by_pool.get(row[0], 0) + 1
    registry_entry = register_snapshot(
        conn,
        entity_type="research_quality_snapshot",
        entity_id=today,
        status="generated",
        source="summarize_research_quality.py",
        relationships={
            "output_rel_path": relative_to_project(out_path),
        },
        payload={
            "row_count": len(rows),
            "counts_by_pool": counts_by_pool,
            "ts_codes": [row[1] for row in rows],
            "output_rel_path": relative_to_project(out_path),
        },
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="研究质量快照已生成，自动转交 Hermes-like 研究代理补充解释。",
        created_by="summarize_research_quality.py",
    )
    conn.commit()
    conn.close()
    log_run(
        "summarize_research_quality.py",
        "success",
        "research quality snapshot generated",
        {
            "rows": len(rows),
            "output": str(out_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Research quality snapshot: {out_path}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
