#!/usr/bin/env python3
"""SMR Risk Engine - Monitors portfolio risk and triggers alerts."""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_external_research import load_external_research_digest
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_portfolio import (
    current_open_positions,
    latest_price,
    load_portfolio_policy,
    projected_costs_by_sector,
    projected_total_cost,
    resolve_sector,
    weekly_loss_snapshot,
)
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
ALERT_DIR = env_or_project_path("SMR_ALERT_DIR", "05_risk", "alerts")


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def count_by_key(items, key):
    counts = {}
    for item in items:
        value = item.get(key)
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_alert(alert_type, severity, message, action, ts_code=None):
    return {
        "alert_type": alert_type,
        "severity": severity,
        "ts_code": ts_code,
        "message": message,
        "action": action,
    }


def build_reference_observations(conn, limit=4):
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entity_latest
        WHERE entity_type='strategy_watch_batch'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row or not row[0]:
        return []

    payload = json.loads(row[0] or "{}")
    items = payload.get("items") or []
    candidates = []
    for item in items:
        pool_types = set(item.get("pool_types") or [])
        if "portfolio_seed" not in pool_types:
            continue
        flow_score = safe_float(item.get("capital_flow_signal_score")) or 0.0
        event_score = safe_float(item.get("event_signal_score")) or 0.0
        priority_score = safe_float((item.get("priority") or {}).get("score")) or 0.0
        if max(flow_score, event_score, priority_score) <= 0:
            continue
        summary = item.get("event_summary") if event_score >= flow_score else item.get("capital_flow_summary")
        if not summary:
            continue
        candidates.append(
            (
                -(max(flow_score, event_score) + priority_score * 0.1),
                item.get("ts_code") or "",
                {
                    "ts_code": item.get("ts_code"),
                    "name": item.get("name") or item.get("ts_code"),
                    "priority_label": (item.get("priority") or {}).get("label"),
                    "capital_flow_summary": item.get("capital_flow_summary"),
                    "event_summary": item.get("event_summary"),
                    "summary": summary,
                },
            )
        )
    candidates.sort()
    observations = []
    for _, _ts_code, item in candidates[:limit]:
        observations.append(
            "{name}：{summary}".format(
                name=item.get("name") or item.get("ts_code") or "-",
                summary=item.get("summary") or "-",
            )
        )
    return observations


def check_position_concentration(conn, policy):
    alerts = []
    portfolio_capital = float(policy["portfolio_capital"])
    positions = current_open_positions(conn)
    if not positions:
        return alerts

    for ts_code, _entry_date, _entry_price, _shares, cost, _target_price, _stop_loss, _thesis, _pnl, _pnl_pct in positions:
        if cost is None:
            continue
        pos_pct = cost / portfolio_capital
        if pos_pct > policy["max_single_position_pct"]:
            alerts.append(
                build_alert(
                    "position_limit",
                    "warning",
                    f"Single position {ts_code} exceeds {policy['max_single_position_pct']*100:.0f}%: {pos_pct*100:.1f}%",
                    "Consider reducing position",
                    ts_code,
                )
            )
    return alerts


def check_total_exposure(conn, policy):
    total_cost = projected_total_cost(conn)
    if total_cost <= 0:
        return []
    total_pct = total_cost / float(policy["portfolio_capital"])
    if total_pct > policy["max_total_exposure_pct"]:
        return [
            build_alert(
                "total_exposure",
                "warning",
                f"Portfolio exposure exceeds {policy['max_total_exposure_pct']*100:.0f}%: {total_pct*100:.1f}%",
                "Pause new entries and trim exposure",
            )
        ]
    return []


def check_sector_concentration(conn, policy):
    alerts = []
    portfolio_capital = float(policy["portfolio_capital"])
    sector_costs = projected_costs_by_sector(conn)
    for sector, cost in sector_costs.items():
        sector_pct = cost / portfolio_capital
        if sector_pct > policy["max_sector_concentration_pct"]:
            alerts.append(
                build_alert(
                    "sector_concentration",
                    "warning",
                    f"Sector {sector} exceeds {policy['max_sector_concentration_pct']*100:.0f}%: {sector_pct*100:.1f}%",
                    "Avoid adding to this sector and review existing positions",
                )
            )
    return alerts


def check_drawdown(conn, policy):
    alerts = []
    positions = current_open_positions(conn)
    for ts_code, _entry_date, entry_price, _shares, _cost, _target_price, _stop_loss, _thesis, _pnl, _pnl_pct in positions:
        current_price = latest_price(conn, ts_code)
        if current_price is None or not entry_price or entry_price <= 0:
            continue
        pnl_pct = (current_price - entry_price) / entry_price
        if pnl_pct < -policy["max_drawdown_pct"]:
            alerts.append(
                build_alert(
                    "drawdown",
                    "critical",
                    f"{ts_code} drawdown exceeds {policy['max_drawdown_pct']*100:.0f}%: {pnl_pct*100:.1f}%",
                    "Consider stop-loss",
                    ts_code,
                )
            )
        elif pnl_pct < -policy["warning_drawdown_pct"]:
            alerts.append(
                build_alert(
                    "drawdown",
                    "warning",
                    f"{ts_code} drawdown exceeds warning line {policy['warning_drawdown_pct']*100:.0f}%: {pnl_pct*100:.1f}%",
                    "Monitor closely",
                    ts_code,
                )
            )
    return alerts


def check_weekly_loss(conn, policy):
    snapshot = weekly_loss_snapshot(conn)
    if snapshot["cost_base"] <= 0:
        return []

    weekly_loss_pct = snapshot["loss"] / snapshot["cost_base"]
    if weekly_loss_pct > policy["max_weekly_loss_pct"]:
        return [
            build_alert(
                "weekly_loss",
                "critical",
                f"Weekly loss exceeds {policy['max_weekly_loss_pct']*100:.0f}%: {weekly_loss_pct*100:.1f}%",
                "Stop adding risk and review all recent positions",
            )
        ]
    if weekly_loss_pct > policy["warning_weekly_loss_pct"]:
        return [
            build_alert(
                "weekly_loss",
                "warning",
                f"Weekly loss exceeds warning line {policy['warning_weekly_loss_pct']*100:.0f}%: {weekly_loss_pct*100:.1f}%",
                "Reduce new risk until losses stabilize",
            )
        ]
    return []


def check_position_metadata(conn):
    alerts = []
    positions = current_open_positions(conn)
    for ts_code, _entry_date, _entry_price, _shares, _cost, target_price, stop_loss, thesis, _pnl, _pnl_pct in positions:
        if not thesis:
            alerts.append(
                build_alert(
                    "thesis_missing",
                    "critical",
                    f"{ts_code} has no recorded thesis",
                    "Fill in thesis immediately or exit the position",
                    ts_code,
                )
            )
        if stop_loss is None:
            alerts.append(
                build_alert(
                    "stop_missing",
                    "warning",
                    f"{ts_code} has no stop-loss recorded",
                    "Add stop-loss discipline for this position",
                    ts_code,
                )
            )
        if target_price is None:
            alerts.append(
                build_alert(
                    "target_missing",
                    "warning",
                    f"{ts_code} has no target price recorded",
                    "Add target logic for this position",
                    ts_code,
                )
            )
    return alerts


def check_stop_target_hits(conn):
    alerts = []
    positions = current_open_positions(conn)
    for ts_code, _entry_date, _entry_price, _shares, _cost, target_price, stop_loss, _thesis, _pnl, _pnl_pct in positions:
        current_price = latest_price(conn, ts_code)
        if current_price is None:
            continue
        if stop_loss is not None and current_price <= stop_loss:
            alerts.append(
                build_alert(
                    "stop_loss_hit",
                    "critical",
                    f"{ts_code} hit stop-loss: current={current_price:.2f}, stop={stop_loss:.2f}",
                    "Review exit immediately",
                    ts_code,
                )
            )
        if target_price is not None and current_price >= target_price:
            alerts.append(
                build_alert(
                    "target_hit",
                    "warning",
                    f"{ts_code} reached target: current={current_price:.2f}, target={target_price:.2f}",
                    "Review partial take-profit",
                    ts_code,
                )
            )
    return alerts


def escalate_existing_alerts(conn, now):
    generated = []
    rows = conn.execute(
        """
        SELECT alert_id, alert_time, severity, ts_code, message
        FROM risk_alert
        WHERE acknowledged=0
        """
    ).fetchall()

    now_dt = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    for alert_id, alert_time, severity, ts_code, message in rows:
        alert_dt = datetime.strptime(alert_time, "%Y-%m-%d %H:%M:%S")
        age_hours = (now_dt - alert_dt).total_seconds() / 3600
        if severity == "warning" and age_hours >= 24:
            conn.execute("UPDATE risk_alert SET severity='critical' WHERE alert_id=?", (alert_id,))
            generated.append(
                build_alert(
                    "alert_escalation",
                    "critical",
                    f"Warning alert escalated after 24h: {message}",
                    "Handle immediately",
                    ts_code,
                )
            )
        elif severity == "critical" and age_hours >= 4:
            generated.append(
                build_alert(
                    "critical_repeat",
                    "critical",
                    f"Critical alert still unacknowledged after 4h: {message}",
                    "Urgent review required",
                    ts_code,
                )
            )
    return generated


def main():
    ALERT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    policy = load_portfolio_policy()
    open_positions = current_open_positions(conn)
    open_position_codes = [row[0] for row in open_positions]
    external_research_digest = load_external_research_digest(
        conn,
        limit=max(5, len(open_position_codes)),
        focus_ts_codes=open_position_codes,
        fallback_to_pool=False,
    )

    all_alerts = []
    all_alerts.extend(check_position_concentration(conn, policy))
    all_alerts.extend(check_total_exposure(conn, policy))
    all_alerts.extend(check_sector_concentration(conn, policy))
    all_alerts.extend(check_drawdown(conn, policy))
    all_alerts.extend(check_weekly_loss(conn, policy))
    all_alerts.extend(check_position_metadata(conn))
    all_alerts.extend(check_stop_target_hits(conn))
    all_alerts.extend(escalate_existing_alerts(conn, now))
    reference_observations = build_reference_observations(conn)

    for alert in all_alerts:
        conn.execute(
            """
            INSERT INTO risk_alert
            (alert_time, alert_type, severity, ts_code, message, action)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (now, alert["alert_type"], alert["severity"], alert.get("ts_code"), alert["message"], alert["action"]),
        )

    alert_file = None
    if all_alerts:
        alert_file = ALERT_DIR / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        lines = [f"# Risk Alert - {now}", ""]
        for alert in all_alerts:
            scope = f" {alert['ts_code']}" if alert.get("ts_code") else ""
            lines.append(f"- **[{alert['severity'].upper()}]** {alert['alert_type']}{scope}: {alert['message']}")
            lines.append(f"  Action: {alert['action']}")
        if reference_observations:
            lines.extend(["", "## 参考组合观察", ""])
            for item in reference_observations:
                lines.append(f"- {item}")
        with open(alert_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        registry_entry = register_snapshot(
            conn,
            entity_type="risk_monitor_snapshot",
            entity_id=now[:10],
            status="alerts_generated",
            source="monitor.py",
            relationships={
                "alert_file_rel_path": relative_to_project(alert_file),
            },
            payload={
                "alert_count": len(all_alerts),
                "counts_by_severity": count_by_key(all_alerts, "severity"),
                "counts_by_type": count_by_key(all_alerts, "alert_type"),
                "open_position_count": len(open_positions),
                "unacknowledged_alert_count": conn.execute(
                    "SELECT COUNT(*) FROM risk_alert WHERE acknowledged=0"
                ).fetchone()[0],
                "alert_file_rel_path": relative_to_project(alert_file),
                "external_research_digest": external_research_digest,
                "reference_observations": reference_observations,
            },
            created_at=now,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="风险快照已更新，自动转交 Hermes-like 风险代理补充解释。",
            created_by="monitor.py",
        )
        conn.commit()
        conn.close()
        log_run(
            "monitor.py",
            "success",
            "risk alerts generated",
            {
                "alert_count": len(all_alerts),
                "alert_file": str(alert_file),
                "handoff_result": handoff_result["reason"],
                "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
            },
        )
        print(f"Generated {len(all_alerts)} alerts, saved to {alert_file}")
        if handoff_result["handoff"]:
            print(
                f"Auto handoff {handoff_result['reason']}: "
                f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
            )
        else:
            print(f"Auto handoff skipped: {handoff_result['reason']}")
    else:
        observation_file = None
        relationships = {}
        if reference_observations:
            observation_file = ALERT_DIR / f"observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            lines = [f"# Risk Observation - {now}", "", "## 参考组合观察", ""]
            for item in reference_observations:
                lines.append(f"- {item}")
            with open(observation_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            relationships["observation_file_rel_path"] = relative_to_project(observation_file)
        registry_entry = register_snapshot(
            conn,
            entity_type="risk_monitor_snapshot",
            entity_id=now[:10],
            status="clear",
            source="monitor.py",
            relationships=relationships,
            payload={
                "alert_count": 0,
                "open_position_count": len(open_positions),
                "unacknowledged_alert_count": conn.execute(
                    "SELECT COUNT(*) FROM risk_alert WHERE acknowledged=0"
                ).fetchone()[0],
                "external_research_digest": external_research_digest,
                "reference_observations": reference_observations,
                "observation_file_rel_path": relative_to_project(observation_file) if observation_file else None,
            },
            created_at=now,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="风险快照已更新，自动转交 Hermes-like 风险代理补充解释。",
            created_by="monitor.py",
        )
        conn.commit()
        conn.close()
        log_run(
            "monitor.py",
            "success",
            "no risk alerts",
            {
                "alert_count": 0,
                "handoff_result": handoff_result["reason"],
                "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
            },
        )
        print("No risk alerts - portfolio within limits")
        if handoff_result["handoff"]:
            print(
                f"Auto handoff {handoff_result['reason']}: "
                f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
            )
        else:
            print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
