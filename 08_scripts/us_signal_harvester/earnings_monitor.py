#!/usr/bin/env python3
"""SMR US signal monitor - deduplicated price/event signals with AH mapping."""

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
from smr_universe import load_active_equity_universe, load_active_us_benchmarks
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
SIGNAL_DIR = project_path("01_data", "us_signals")

SURGE_THRESHOLD = 3.0
STRONG_SURGE_THRESHOLD = 7.0


def ah_mapping(conn):
    equities = load_active_equity_universe(conn, include_seed=True)
    mapping = {}
    for ts_code, meta in equities.items():
        mapping.setdefault(meta["sector"], []).append(ts_code)
    return mapping


def infer_signal_type(pct_chg):
    if pct_chg >= STRONG_SURGE_THRESHOLD:
        return "strong_price_surge"
    if pct_chg >= SURGE_THRESHOLD:
        return "price_surge"
    if pct_chg <= -STRONG_SURGE_THRESHOLD:
        return "strong_price_drop"
    if pct_chg <= -SURGE_THRESHOLD:
        return "price_drop"
    return None


def infer_ah_impact(sector, pct_chg):
    if pct_chg >= STRONG_SURGE_THRESHOLD:
        return f"{sector} 链条强正向映射"
    if pct_chg >= SURGE_THRESHOLD:
        return f"{sector} 链条偏正向映射"
    if pct_chg <= -STRONG_SURGE_THRESHOLD:
        return f"{sector} 链条强负向映射"
    if pct_chg <= -SURGE_THRESHOLD:
        return f"{sector} 链条偏负向映射"
    return None


def check_price_signals(conn, us_benchmarks):
    sector_to_ah = ah_mapping(conn)
    alerts = []
    for symbol, meta in us_benchmarks.items():
        name = meta["name"]
        sector = meta["sector"]
        hist = conn.execute(
            """
            SELECT trade_date, close, vol
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date DESC
            LIMIT 5
            """,
            (symbol,),
        ).fetchall()
        if len(hist) < 2:
            print(f"  {symbol} {name}: insufficient local data")
            continue

        latest = hist[0]
        prev = hist[1]
        if prev[1] in (None, 0):
            continue

        pct_chg = round((latest[1] - prev[1]) / prev[1] * 100, 2)
        signal_type = infer_signal_type(pct_chg)
        if not signal_type:
            continue

        related_ah = ",".join(sorted(sector_to_ah.get(sector, []))[:8])
        direction = "大涨" if pct_chg > 0 else "大跌"
        alerts.append(
            {
                "signal_time": f"{latest[0]} 00:00:00",
                "trade_date": latest[0],
                "symbol": symbol,
                "name": name,
                "sector": sector,
                "signal_type": signal_type,
                "title": f"{name}({symbol}) {direction} {pct_chg:.1f}%",
                "summary": f"日期: {latest[0]}, 收盘价: ${latest[1]:.2f}, 成交量: {latest[2]:,.0f}, sector={sector}",
                "pct_chg": pct_chg,
                "ah_impact": infer_ah_impact(sector, pct_chg),
                "related_ah": related_ah,
                "source_url": None,
            }
        )
    return alerts


def is_duplicate_signal(conn, alert):
    row = conn.execute(
        """
        SELECT 1
        FROM us_signal
        WHERE symbol=?
          AND signal_type=?
          AND substr(signal_time, 1, 10)=?
        LIMIT 1
        """,
        (alert["symbol"], alert["signal_type"], alert["trade_date"]),
    ).fetchone()
    return bool(row)


def save_signals(conn, alerts):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    signal_file = None

    for alert in alerts:
        if is_duplicate_signal(conn, alert):
            continue
        conn.execute(
            """
            INSERT INTO us_signal
            (signal_time, symbol, signal_type, title, summary, ah_impact, related_ah, source_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert["signal_time"],
                alert["symbol"],
                alert["signal_type"],
                alert["title"],
                alert["summary"],
                alert["ah_impact"],
                alert["related_ah"],
                alert["source_url"],
                now,
            ),
        )
        saved.append(alert)

    if saved:
        signal_file = SIGNAL_DIR / f"{datetime.now().strftime('%Y%m%d')}.md"
        with open(signal_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {now}\n\n")
            for alert in saved:
                emoji = "🔴" if alert["pct_chg"] < 0 else "🟢"
                related = alert["related_ah"] or "-"
                impact = alert["ah_impact"] or "-"
                f.write(f"- {emoji} **{alert['title']}** — {alert['summary']} | impact={impact} | related_ah={related}\n")

    conn.commit()
    return saved, signal_file


def main():
    conn = sqlite3.connect(DB_PATH)
    us_benchmarks = load_active_us_benchmarks(conn)
    print("Checking US benchmark price signals...")
    alerts = check_price_signals(conn, us_benchmarks)
    saved, signal_file = save_signals(conn, alerts)

    execution_date = datetime.now().strftime("%Y-%m-%d")
    registry_entry = register_snapshot(
        conn,
        entity_type="us_signal_snapshot",
        entity_id=execution_date,
        status="signals_saved" if saved else "no_change",
        source="earnings_monitor.py",
        relationships={
            "signal_file_rel_path": relative_to_project(signal_file) if signal_file else None,
        },
        payload={
            "saved_count": len(saved),
            "symbols": [alert["symbol"] for alert in saved],
            "signal_types": sorted({alert["signal_type"] for alert in saved}),
            "sectors": sorted({alert["sector"] for alert in saved}),
            "signal_file_rel_path": relative_to_project(signal_file) if signal_file else None,
            "total_us_signal_rows": conn.execute("SELECT COUNT(*) FROM us_signal").fetchone()[0],
        },
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="美股信号快照已更新，必要时自动转交 Hermes-like 研究代理补充解释。",
        created_by="earnings_monitor.py",
    )
    conn.commit()

    if saved:
        log_run(
            "earnings_monitor.py",
            "success",
            "us signals saved",
            {
                "saved_count": len(saved),
                "symbols": [alert["symbol"] for alert in saved],
                "handoff_result": handoff_result["reason"],
                "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
            },
        )
        print(f"Saved {len(saved)} significant signals:")
        for alert in saved:
            emoji = "🔴" if alert["pct_chg"] < 0 else "🟢"
            print(f"  {emoji} {alert['title']} -> {alert['ah_impact']}")
    else:
        log_run(
            "earnings_monitor.py",
            "success",
            "no new significant price signals",
            {
                "saved_count": 0,
                "handoff_result": handoff_result["reason"],
                "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
            },
        )
        print("No new significant price signals detected")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")

    conn.close()


if __name__ == "__main__":
    main()
