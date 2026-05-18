#!/usr/bin/env python3
"""Upsert SMR cron jobs in OpenClaw jobs.json."""

import json
import uuid
from datetime import datetime
from pathlib import Path

CRON_PATH = Path("/Users/apple/.openclaw/cron/jobs.json")


def now_ms():
    return int(datetime.now().timestamp() * 1000)


def desired_jobs():
    current_ms = now_ms()
    return [
        {
            "agentId": "smr-analyst",
            "name": "SMR-A+H行情采集",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "30 15 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "执行A+H动态收盘链路：1) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/stock_pool/sync_watchlist.py 2) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only 3) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only 4) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/trend.py 5) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/fundamental.py 6) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py 7) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/research/generate_trend_batch.py 8) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/stock_pool/reconcile_dynamic_pool.py",
                "thinking": "low",
                "timeoutSeconds": 1800,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-analyst",
            "name": "SMR-美股行情采集",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "0 6 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "执行美股动态晨间链路：1) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/stock_pool/sync_watchlist.py 2) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only 3) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/us_signal_harvester/earnings_monitor.py 4) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py 5) 如有显著变化，再运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/stock_pool/reconcile_dynamic_pool.py",
                "thinking": "low",
                "timeoutSeconds": 1200,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-analyst",
            "name": "SMR-因子计算",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "30 16 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "执行补充因子与动态池重建：1) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/trend.py 2) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/fundamental.py 3) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py 4) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/research/generate_trend_batch.py 5) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/stock_pool/reconcile_dynamic_pool.py",
                "thinking": "low",
                "timeoutSeconds": 1200,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-brief-writer",
            "name": "SMR-盘前简报",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "0 9 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "撰写盘前简报：1) 读取01_data/us_signals/中的美股信号 2) 读取因子数据 3) 读取 stock_pool_current 中当前有效 watchlist/candidate/recommended 4) 撰写包含美股联动和动态股票池变化的盘前简报 5) 保存到06_reports/daily/",
                "thinking": "medium",
                "timeoutSeconds": 900,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-portfolio-mgr",
            "name": "SMR-持仓复盘",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "30 19 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "执行持仓复盘：1) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/portfolio/pnl.py 更新盈亏 2) 检查每笔持仓的 thesis、止损、目标位和行业集中度 3) 输出调仓建议",
                "thinking": "medium",
                "timeoutSeconds": 900,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-risk-controller",
            "name": "SMR-风控日报",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "0 21 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "执行风控检查：1) 运行 python3 /Users/apple/Documents/同行资本二级市场/08_scripts/risk_engine/monitor.py 2) 如有预警，写入05_risk/alerts/ 3) 检查单票/总暴露/行业集中/周亏损/止损位/目标位",
                "thinking": "medium",
                "timeoutSeconds": 900,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-brief-writer",
            "name": "SMR-日报撰写",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "30 20 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "撰写每日市场复盘日报：1) 读取当日行情数据 2) 读取持仓盈亏 3) 读取风控状态 4) 读取研究进展 5) 读取 stock_pool_current 和动态池快照 6) 撰写包含免责声明的日报 7) 保存到06_reports/daily/",
                "thinking": "medium",
                "timeoutSeconds": 1200,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
        {
            "agentId": "smr-lead",
            "name": "SMR-次日计划",
            "enabled": True,
            "schedule": {"kind": "cron", "expr": "0 22 * * 1-5", "tz": "Asia/Shanghai", "staggerMs": 0},
            "sessionTarget": "isolated",
            "wakeMode": "now",
            "payload": {
                "kind": "agentTurn",
                "message": "制定次日研究/操作计划：1) 回顾今日日报和风控状态 2) 检查动态股票池新增 candidate/recommended 3) 检查是否有待处理的研究触发 4) 检查美股财报日历 5) 更新00_control/dispatch_board.md",
                "thinking": "medium",
                "timeoutSeconds": 900,
            },
            "delivery": {"mode": "none"},
            "_timestamps": current_ms,
        },
    ]


def main():
    if not CRON_PATH.exists():
        raise SystemExit(f"Missing cron jobs file: {CRON_PATH}")

    with open(CRON_PATH, "r", encoding="utf-8") as f:
        cron_data = json.load(f)

    jobs = cron_data.setdefault("jobs", [])
    existing_by_name = {job["name"]: job for job in jobs}

    added = 0
    updated = 0
    for desired in desired_jobs():
        name = desired["name"]
        timestamp = desired.pop("_timestamps")
        existing = existing_by_name.get(name)
        if existing:
            existing.update(
                {
                    "agentId": desired["agentId"],
                    "name": desired["name"],
                    "enabled": desired["enabled"],
                    "schedule": desired["schedule"],
                    "sessionTarget": desired["sessionTarget"],
                    "wakeMode": desired["wakeMode"],
                    "payload": desired["payload"],
                    "delivery": desired["delivery"],
                    "updatedAtMs": timestamp,
                }
            )
            updated += 1
            print(f"  Updated: {name} ({desired['schedule']['expr']})")
        else:
            job = {
                "id": str(uuid.uuid4()),
                "createdAtMs": timestamp,
                "updatedAtMs": timestamp,
                **desired,
            }
            jobs.append(job)
            added += 1
            print(f"  Added: {name} ({desired['schedule']['expr']})")

    with open(CRON_PATH, "w", encoding="utf-8") as f:
        json.dump(cron_data, f, indent=2, ensure_ascii=False)

    total = len(jobs)
    smr_total = sum(1 for job in jobs if job.get("name", "").startswith("SMR-"))
    print(f"\nAdded {added}, updated {updated} SMR cron jobs. Total: {total} jobs ({smr_total} SMR)")


if __name__ == "__main__":
    main()
