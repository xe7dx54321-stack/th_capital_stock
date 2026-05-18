#!/usr/bin/env python3
"""Rebuild live stock pools from seed universe, research decisions, and latest factor signals."""

import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

ROOT = project_path()
DB_PATH = project_path("01_data", "db", "smr.db")
WATCHLIST_PATH = project_path("00_control", "watchlist_registry.md")
OUTPUT_DIR = project_path("03_stock_pool", "watchlist")

POSITIVE_POOLS = {"watchlist", "candidate", "recommended"}
DROP_POOLS = {"drop", "remove", "inactive", "out", "archive"}
WATCHLIST_SIGNAL_THRESHOLD = 1.0


def normalize_ah_code(raw_code, market):
    code = raw_code.strip()
    if market == "HK":
        return f"{code}.HK"
    if code.startswith(("0", "3")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SH"


def ensure_pool_views(conn):
    conn.executescript(
        """
        DROP VIEW IF EXISTS stock_pool_latest;
        CREATE VIEW stock_pool_latest AS
        WITH ranked AS (
            SELECT
                rowid AS event_rowid,
                pool_type,
                ts_code,
                sector,
                added_date,
                added_reason,
                score,
                status,
                ROW_NUMBER() OVER (
                    PARTITION BY pool_type, ts_code
                    ORDER BY datetime(added_date) DESC, rowid DESC
                ) AS rn
            FROM stock_pool
        )
        SELECT
            pool_type,
            ts_code,
            sector,
            added_date,
            added_reason,
            score,
            status
        FROM ranked
        WHERE rn = 1;

        DROP VIEW IF EXISTS stock_pool_current;
        CREATE VIEW stock_pool_current AS
        SELECT
            pool_type,
            ts_code,
            sector,
            added_date,
            added_reason,
            score,
            status
        FROM stock_pool_latest
        WHERE status = 'active';
        """
    )


def ensure_research_decision_views(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_decision (
            report_id TEXT PRIMARY KEY,
            ts_code TEXT NOT NULL,
            report_type TEXT NOT NULL,
            sector TEXT,
            title TEXT,
            decision_time TEXT NOT NULL,
            decision_priority INTEGER NOT NULL,
            suggested_pool TEXT NOT NULL,
            thesis_strength TEXT,
            customer_evidence TEXT,
            order_evidence TEXT,
            commercialization_evidence TEXT,
            valuation_risk TEXT,
            open_gap_count INTEGER,
            research_quality_score REAL,
            reason TEXT,
            file_path TEXT
        )
        """
    )
    desired_columns = {
        "customer_evidence": "TEXT",
        "order_evidence": "TEXT",
        "commercialization_evidence": "TEXT",
        "valuation_risk": "TEXT",
        "open_gap_count": "INTEGER",
        "research_quality_score": "REAL",
    }
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(research_decision)").fetchall()}
    for column_name, column_type in desired_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE research_decision ADD COLUMN {column_name} {column_type}")
    conn.executescript(
        """
        DROP VIEW IF EXISTS research_decision_latest;
        CREATE VIEW research_decision_latest AS
        WITH ranked AS (
            SELECT
                report_id,
                ts_code,
                report_type,
                sector,
                title,
                decision_time,
                decision_priority,
                suggested_pool,
                thesis_strength,
                customer_evidence,
                order_evidence,
                commercialization_evidence,
                valuation_risk,
                open_gap_count,
                research_quality_score,
                reason,
                file_path,
                ROW_NUMBER() OVER (
                    PARTITION BY ts_code
                    ORDER BY decision_priority DESC, datetime(decision_time) DESC, rowid DESC
                ) AS rn
            FROM research_decision
        )
        SELECT
            report_id,
            ts_code,
            report_type,
            sector,
            title,
            decision_time,
            decision_priority,
            suggested_pool,
            thesis_strength,
            customer_evidence,
            order_evidence,
            commercialization_evidence,
            valuation_risk,
            open_gap_count,
            research_quality_score,
            reason,
            file_path
        FROM ranked
        WHERE rn = 1;
        """
    )


def parse_seed_registry():
    current_market = None
    rows = {}

    for line in WATCHLIST_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "## A股标的":
            current_market = "A"
            continue
        if stripped == "## H股标的":
            current_market = "HK"
            continue
        if stripped == "## 美股对标（仅跟踪，不投资）":
            current_market = "US"
            continue
        if not stripped.startswith("|"):
            continue
        if "Code" in stripped or "Symbol" in stripped or stripped.startswith("|------"):
            continue

        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if current_market == "US":
            continue
        if len(parts) != 5 or current_market not in {"A", "HK"}:
            continue

        raw_code, name, sector, _pool_label, registry_added = parts
        ts_code = normalize_ah_code(raw_code, current_market)
        rows[ts_code] = {
            "name": name,
            "sector": sector,
            "registry_added": registry_added,
            "market": current_market,
        }

    return rows


def load_factor_snapshots(conn):
    latest_factor_date = conn.execute("SELECT max(trade_date) FROM factor_daily").fetchone()[0]
    latest_daily_date = conn.execute("SELECT max(trade_date) FROM daily_bar").fetchone()[0]

    factor_rows = conn.execute(
        """
        SELECT ts_code, factor_name, factor_value
        FROM factor_daily
        WHERE trade_date = ?
        """,
        (latest_factor_date,),
    ).fetchall()

    daily_rows = conn.execute(
        """
        SELECT ts_code, close, pct_chg
        FROM daily_bar
        WHERE trade_date = ?
        """,
        (latest_daily_date,),
    ).fetchall()

    snapshots = defaultdict(lambda: {"factor_date": latest_factor_date, "trade_date": latest_daily_date, "us_links": {}})
    for ts_code, factor_name, factor_value in factor_rows:
        if factor_name.startswith("us_linkage_"):
            snapshots[ts_code]["us_links"][factor_name.replace("us_linkage_", "").upper()] = factor_value
        else:
            snapshots[ts_code][factor_name] = factor_value

    for ts_code, close, pct_chg in daily_rows:
        snapshots[ts_code]["close"] = close
        snapshots[ts_code]["pct_chg"] = pct_chg

    return dict(snapshots)


def parse_suggested_pool(file_path):
    path = normalize_project_path(file_path)
    card_text = path.read_text(encoding="utf-8")

    if "report_type: recommendation" in card_text:
        return "recommended"

    match = re.search(r"^## Suggested Pool:\s*([A-Za-z_]+)\s*$", card_text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip().lower()

    conclusion_path = path.with_name("conclusion.md")
    if conclusion_path.exists():
        conclusion_text = conclusion_path.read_text(encoding="utf-8")
        match = re.search(r"suggested_pool:\s*([A-Za-z_]+)", conclusion_text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()

    return None


def parse_thesis_strength(file_path):
    path = normalize_project_path(file_path)
    card_text = path.read_text(encoding="utf-8")

    match = re.search(r"^## Thesis Strength\s*$\s*^([A-Za-z_]+)\s*$", card_text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip().lower()

    conclusion_path = path.with_name("conclusion.md")
    if conclusion_path.exists():
        conclusion_text = conclusion_path.read_text(encoding="utf-8")
        match = re.search(r"thesis_strength:\s*([A-Za-z_]+)", conclusion_text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()

    return None


def parse_reasoning(file_path):
    path = normalize_project_path(file_path)
    card_text = path.read_text(encoding="utf-8")

    match = re.search(r"Reasoning:\s*(.+)", card_text)
    if match:
        return match.group(1).strip()

    thesis_match = re.search(r"## Thesis\s+(.+?)(?:\n## |\Z)", card_text, flags=re.DOTALL)
    if thesis_match:
        return " ".join(line.strip() for line in thesis_match.group(1).splitlines() if line.strip())[:400]

    return None


def parse_named_field(file_path, field_name):
    card_path = normalize_project_path(file_path)
    texts = []
    conclusion_path = card_path.with_name("conclusion.md")
    if conclusion_path.exists():
        texts.append(conclusion_path.read_text(encoding="utf-8"))
    texts.append(card_path.read_text(encoding="utf-8"))

    patterns = [
        rf"^- {re.escape(field_name)}:\s*(.+)\s*$",
        rf"^{re.escape(field_name)}:\s*(.+)\s*$",
    ]
    for text in texts:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.MULTILINE)
            if match:
                return match.group(1).strip()
    return None


def decision_priority(report_type, file_path):
    if report_type == "recommendation":
        return 3
    if "deep_research" in file_path:
        return 2
    return 1


def sync_research_decisions(conn):
    ensure_research_decision_views(conn)
    rows = conn.execute(
        """
        SELECT report_id, report_type, sector, title, ts_codes, created_at, file_path
        FROM research_index
        WHERE report_type IN ('stock', 'recommendation')
          AND instr(ts_codes, ',') = 0
        """
    ).fetchall()

    parsed_rows = []
    for report_id, report_type, sector, title, ts_code, created_at, file_path in rows:
        suggested_pool = parse_suggested_pool(file_path)
        if not suggested_pool:
            continue
        parsed_rows.append(
            {
                "report_id": report_id,
                "report_type": report_type,
                "sector": sector,
                "title": title,
                "ts_code": ts_code,
                "created_at": created_at,
                "file_path": str(normalize_project_path(file_path)),
                "decision_priority": decision_priority(report_type, file_path),
                "suggested_pool": suggested_pool,
                "thesis_strength": parse_thesis_strength(file_path),
                "customer_evidence": parse_named_field(file_path, "customer_evidence"),
                "order_evidence": parse_named_field(file_path, "order_evidence"),
                "commercialization_evidence": parse_named_field(file_path, "commercialization_evidence"),
                "valuation_risk": parse_named_field(file_path, "valuation_risk"),
                "open_gap_count": int(parse_named_field(file_path, "open_gap_count")) if parse_named_field(file_path, "open_gap_count") else None,
                "research_quality_score": float(parse_named_field(file_path, "research_quality_score")) if parse_named_field(file_path, "research_quality_score") else None,
                "reason": parse_reasoning(file_path),
            }
        )

    parsed_rows.sort(key=lambda item: (item["ts_code"], item["decision_priority"], item["created_at"]), reverse=True)
    quality_fields = [
        "customer_evidence",
        "order_evidence",
        "commercialization_evidence",
        "valuation_risk",
        "open_gap_count",
        "research_quality_score",
    ]
    fallback_quality = {}
    for item in sorted(parsed_rows, key=lambda item: (item["ts_code"], item["decision_priority"], item["created_at"]), reverse=True):
        ts_code = item["ts_code"]
        fallback_quality.setdefault(ts_code, {})
        for field in quality_fields:
            if field not in fallback_quality[ts_code] and item.get(field) not in (None, ""):
                fallback_quality[ts_code][field] = item[field]

    synced = 0
    for item in parsed_rows:
        ts_code = item["ts_code"]
        merged = item.copy()
        for field in quality_fields:
            if merged.get(field) in (None, "") and field in fallback_quality.get(ts_code, {}):
                merged[field] = fallback_quality[ts_code][field]
        conn.execute(
            """
            INSERT OR REPLACE INTO research_decision
            (report_id, ts_code, report_type, sector, title, decision_time, decision_priority, suggested_pool, thesis_strength, customer_evidence, order_evidence, commercialization_evidence, valuation_risk, open_gap_count, research_quality_score, reason, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                merged["report_id"],
                ts_code,
                merged["report_type"],
                merged["sector"],
                merged["title"],
                merged["created_at"],
                merged["decision_priority"],
                merged["suggested_pool"],
                merged["thesis_strength"],
                merged["customer_evidence"],
                merged["order_evidence"],
                merged["commercialization_evidence"],
                merged["valuation_risk"],
                merged["open_gap_count"],
                merged["research_quality_score"],
                merged["reason"],
                merged["file_path"],
            ),
        )
        synced += 1

    ensure_research_decision_views(conn)
    return synced


def load_latest_decisions(conn):
    rows = conn.execute(
        """
        SELECT report_id, report_type, sector, title, ts_code, decision_time, file_path, suggested_pool, thesis_strength, customer_evidence, order_evidence, commercialization_evidence, valuation_risk, open_gap_count, research_quality_score, reason
        FROM research_decision_latest
        """
    ).fetchall()

    decisions = {}
    for report_id, report_type, sector, title, ts_code, decision_time, file_path, suggested_pool, thesis_strength, customer_evidence, order_evidence, commercialization_evidence, valuation_risk, open_gap_count, research_quality_score, reason in rows:
        decisions[ts_code] = {
            "report_id": report_id,
            "report_type": report_type,
            "sector": sector,
            "title": title,
            "created_at": decision_time,
            "file_path": file_path,
            "suggested_pool": suggested_pool,
            "thesis_strength": thesis_strength,
            "customer_evidence": customer_evidence,
            "order_evidence": order_evidence,
            "commercialization_evidence": commercialization_evidence,
            "valuation_risk": valuation_risk,
            "open_gap_count": open_gap_count,
            "research_quality_score": research_quality_score,
            "reason": reason,
        }
    return decisions


def latest_pool_rows(conn):
    rows = conn.execute(
        """
        SELECT pool_type, ts_code, sector, added_date, added_reason, score, status
        FROM stock_pool_latest
        WHERE pool_type IN ('watchlist', 'candidate', 'recommended', 'seed')
        """
    ).fetchall()
    return {
        (pool_type, ts_code): {
            "sector": sector,
            "added_date": added_date,
            "added_reason": added_reason,
            "score": score,
            "status": status,
        }
        for pool_type, ts_code, sector, added_date, added_reason, score, status in rows
    }


def compute_watchlist_score(snapshot):
    trend_strength = snapshot.get("trend_strength") or 0.0
    pct_chg = snapshot.get("pct_chg") or 0.0
    us_link_total = sum(snapshot.get("us_links", {}).values())
    return round(trend_strength * 2.0 + max(pct_chg, 0.0) * 0.1 + min(us_link_total, 30.0) * 0.1, 2)


def compute_research_score(snapshot, explicit_pool):
    base = compute_watchlist_score(snapshot)
    if explicit_pool == "candidate":
        return round(max(base, 7.0), 2)
    if explicit_pool == "recommended":
        return round(max(base, 8.5), 2)
    return round(base, 2)


def recommendation_quality_gate(decision):
    score = decision.get("research_quality_score")
    order_evidence = (decision.get("order_evidence") or "").lower()
    commercialization_evidence = (decision.get("commercialization_evidence") or "").lower()

    if score is None:
        return False, "missing research_quality_score"
    if score < 8.0:
        return False, f"research_quality_score={score:.1f} < 8.0"
    if order_evidence in {"weak", "none", "unknown"}:
        return False, f"order_evidence={order_evidence or 'missing'}"
    if commercialization_evidence in {"weak", "none", "unknown"}:
        return False, f"commercialization_evidence={commercialization_evidence or 'missing'}"
    return True, "quality gate pass"


def upsert_pool_event(conn, pool_type, ts_code, sector, event_time, reason, status, score=None):
    conn.execute(
        """
        INSERT OR REPLACE INTO stock_pool
        (pool_type, ts_code, sector, added_date, added_reason, score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (pool_type, ts_code, sector, event_time, reason, score, status),
    )


def sync_watchlist_state(conn, ts_code, sector, explicit_decision, snapshot, event_time):
    trend_strength = snapshot.get("trend_strength") if snapshot else None
    signal_positive = trend_strength is not None and trend_strength >= WATCHLIST_SIGNAL_THRESHOLD

    if explicit_decision in DROP_POOLS:
        upsert_pool_event(
            conn,
            "watchlist",
            ts_code,
            sector,
            event_time,
            f"research requested out-pool ({explicit_decision})",
            "inactive",
            None,
        )
        return

    if explicit_decision in POSITIVE_POOLS:
        reason = f"research-driven pool sync: latest decision suggests {explicit_decision}"
        score = compute_research_score(snapshot or {}, explicit_decision)
        upsert_pool_event(conn, "watchlist", ts_code, sector, event_time, reason, "active", score)
        return

    if signal_positive:
        reason = (
            "dynamic signal keepalive: "
            f"trend_strength={trend_strength:.0f}, pct_chg={(snapshot.get('pct_chg') or 0):.2f}%"
        )
        score = compute_watchlist_score(snapshot)
        upsert_pool_event(conn, "watchlist", ts_code, sector, event_time, reason, "active", score)
        return

    upsert_pool_event(
        conn,
        "watchlist",
        ts_code,
        sector,
        event_time,
        "dynamic out-pool: no active research support and trend below threshold",
        "inactive",
        None,
    )


def sync_research_pool_state(conn, pool_type, ts_code, sector, should_be_active, explicit_decision, snapshot, event_time, decision=None):
    if should_be_active:
        if pool_type == "recommended":
            passed, gate_reason = recommendation_quality_gate(decision or {})
            if not passed:
                upsert_pool_event(
                    conn,
                    pool_type,
                    ts_code,
                    sector,
                    event_time,
                    f"recommended blocked by research quality gate: {gate_reason}",
                    "inactive",
                    None,
                )
                return
        reason = f"latest research decision => {explicit_decision}"
        score = compute_research_score(snapshot or {}, explicit_decision)
        upsert_pool_event(conn, pool_type, ts_code, sector, event_time, reason, "active", score)
    else:
        upsert_pool_event(
            conn,
            pool_type,
            ts_code,
            sector,
            event_time,
            f"latest research decision is not {pool_type}",
            "inactive",
            None,
        )


def friendly_name(ts_code, seed_meta, decision):
    if ts_code in seed_meta:
        return seed_meta[ts_code]["name"]
    if decision:
        return decision["title"].split()[0]
    return ts_code


def write_snapshot(conn, seed_meta, decisions, event_day):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = OUTPUT_DIR / f"{event_day}_dynamic_watchlist.md"

    active_rows = conn.execute(
        """
        SELECT pool_type, ts_code, sector, score, added_reason
        FROM stock_pool_current
        WHERE pool_type IN ('watchlist', 'candidate', 'recommended')
        ORDER BY
            CASE pool_type
                WHEN 'recommended' THEN 1
                WHEN 'candidate' THEN 2
                ELSE 3
            END,
            score DESC,
            ts_code
        """
    ).fetchall()
    active_by_pool = defaultdict(list)
    for row in active_rows:
        active_by_pool[row[0]].append(row)

    removed_today = conn.execute(
        """
        SELECT pool_type, ts_code, sector, added_reason
        FROM stock_pool_latest
        WHERE pool_type IN ('watchlist', 'candidate', 'recommended')
          AND status='inactive'
          AND substr(added_date, 1, 10)=?
        ORDER BY pool_type, ts_code
        """,
        (event_day,),
    ).fetchall()

    lines = [
        "# SMR Dynamic Stock Pool Snapshot",
        "",
        f"- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- source_seed_registry: {WATCHLIST_PATH}",
        "- logic: latest structured research decision overrides; otherwise latest trend signal keeps or drops watchlist names",
        "",
        "## Current Counts",
        "",
    ]

    count_rows = conn.execute(
        """
        SELECT pool_type, count(*) AS cnt
        FROM stock_pool_current
        WHERE pool_type IN ('seed', 'watchlist', 'candidate', 'recommended', 'us_benchmark')
        GROUP BY pool_type
        ORDER BY pool_type
        """
    ).fetchall()
    for pool_type, cnt in count_rows:
        lines.append(f"- {pool_type}: {cnt}")

    for pool_type in ("recommended", "candidate", "watchlist"):
        lines.extend(
            [
                "",
                f"## Active {pool_type}",
                "",
                "| ts_code | name | sector | score | reason |",
                "|---------|------|--------|------:|--------|",
            ]
        )
        for _pool_type, ts_code, sector, score, reason in active_by_pool.get(pool_type, []):
            name = friendly_name(ts_code, seed_meta, decisions.get(ts_code))
            lines.append(f"| {ts_code} | {name} | {sector or ''} | {score or 0:.2f} | {reason} |")
        if not active_by_pool.get(pool_type):
            lines.append("| - | - | - | - | none |")

    lines.extend(
        [
            "",
            "## Out-Pool Events Today",
            "",
            "| pool_type | ts_code | name | sector | reason |",
            "|-----------|---------|------|--------|--------|",
        ]
    )
    for pool_type, ts_code, sector, reason in removed_today:
        name = friendly_name(ts_code, seed_meta, decisions.get(ts_code))
        lines.append(f"| {pool_type} | {ts_code} | {name} | {sector or ''} | {reason} |")
    if not removed_today:
        lines.append("| - | - | - | - | none |")

    snapshot_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return snapshot_path


def active_codes_by_pool(conn):
    rows = conn.execute(
        """
        SELECT pool_type, ts_code
        FROM stock_pool_current
        WHERE pool_type IN ('watchlist', 'candidate', 'recommended')
        ORDER BY pool_type, ts_code
        """
    ).fetchall()
    grouped = defaultdict(list)
    for pool_type, ts_code in rows:
        grouped[pool_type].append(ts_code)
    return dict(grouped)


def main():
    event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_day = event_time[:10]
    seed_meta = parse_seed_registry()

    conn = sqlite3.connect(DB_PATH)
    ensure_pool_views(conn)
    synced_decisions = sync_research_decisions(conn)
    factor_snapshots = load_factor_snapshots(conn)
    decisions = load_latest_decisions(conn)
    latest_rows = latest_pool_rows(conn)

    live_codes = set(seed_meta) | set(decisions)
    live_codes.update(ts_code for (_, ts_code) in latest_rows)

    for ts_code in sorted(live_codes):
        decision = decisions.get(ts_code)
        explicit_pool = decision["suggested_pool"] if decision else None
        sector = (
            (decision or {}).get("sector")
            or seed_meta.get(ts_code, {}).get("sector")
            or latest_rows.get(("watchlist", ts_code), {}).get("sector")
            or latest_rows.get(("candidate", ts_code), {}).get("sector")
            or latest_rows.get(("recommended", ts_code), {}).get("sector")
        )
        snapshot = factor_snapshots.get(ts_code, {})

        sync_watchlist_state(conn, ts_code, sector, explicit_pool, snapshot, event_time)

        if explicit_pool is not None:
            sync_research_pool_state(
                conn,
                "candidate",
                ts_code,
                sector,
                should_be_active=(explicit_pool == "candidate"),
                explicit_decision=explicit_pool,
                snapshot=snapshot,
                event_time=event_time,
                decision=decision,
            )
            sync_research_pool_state(
                conn,
                "recommended",
                ts_code,
                sector,
                should_be_active=(explicit_pool == "recommended"),
                explicit_decision=explicit_pool,
                snapshot=snapshot,
                event_time=event_time,
                decision=decision,
            )

    ensure_pool_views(conn)
    snapshot_path = write_snapshot(conn, seed_meta, decisions, event_day)

    count_rows = conn.execute(
        """
        SELECT pool_type, count(*) AS cnt
        FROM stock_pool_current
        WHERE pool_type IN ('seed', 'watchlist', 'candidate', 'recommended', 'us_benchmark')
        GROUP BY pool_type
        ORDER BY pool_type
        """
    ).fetchall()
    active_codes = active_codes_by_pool(conn)
    counts_payload = {pool_type: cnt for pool_type, cnt in count_rows}
    registry_entry = register_snapshot(
        conn,
        entity_type="dynamic_pool_snapshot",
        entity_id=event_day,
        status="reconciled",
        source="reconcile_dynamic_pool.py",
        relationships={
            "event_time": event_time,
            "snapshot_rel_path": relative_to_project(snapshot_path),
        },
        payload={
            "counts": counts_payload,
            "structured_decisions": synced_decisions,
            "live_code_count": len(live_codes),
            "active_codes_by_pool": active_codes,
        },
        created_at=event_time,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="动态池快照已更新，自动转交 Hermes-like 研究代理补充池子变化解释。",
        created_by="reconcile_dynamic_pool.py",
    )
    conn.commit()
    conn.close()

    counts = ", ".join(f"{pool_type}={cnt}" for pool_type, cnt in count_rows)
    log_run(
        "reconcile_dynamic_pool.py",
        "success",
        "dynamic pool reconciled",
        {
            "counts": counts_payload,
            "structured_decisions": synced_decisions,
            "snapshot": str(snapshot_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Reconciled dynamic stock pools: {counts}")
    print(f"Structured research decisions synced: {synced_decisions}")
    print(f"Snapshot: {snapshot_path}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
