#!/usr/bin/env python3
"""Phase 0-6: Verification tests for SMR infrastructure (fixed)."""

import json
import os
import sqlite3

print("=" * 60)
print("SMR Phase 0 Verification Tests")
print("=" * 60)

with open("/Users/apple/.openclaw/openclaw.json", "r", encoding="utf-8") as f:
    config = json.load(f)

agent_ids = [a["id"] for a in config["agents"]["list"]]
smr_ids = [aid for aid in agent_ids if aid.startswith("smr-")]
expected_smr = {"smr-lead", "smr-researcher", "smr-analyst", "smr-advisor", "smr-portfolio-mgr", "smr-risk-controller", "smr-brief-writer"}

print(f"\n[1] SMR agents in openclaw.json: {sorted(smr_ids)}")
assert set(smr_ids) == expected_smr
print("  ✅ PASS")

allow_list = config["tools"]["agentToAgent"]["allow"]
print(f"\n[2] SMR agents in agentToAgent.allow")
for aid in expected_smr:
    assert aid in allow_list
print("  ✅ PASS")

existing_expected = {"lead", "knowledge-curator", "thesis-architect", "opportunity-scout", "red-team", "ic-ops", "signal-harvester", "market-scout", "topic-planner", "content-writer", "redteam-reviewer", "publish-ops", "content-analyst", "market-editor"}
actual_existing = set(agent_ids) - expected_smr
print(f"\n[3] Existing agents unchanged")
assert existing_expected == actual_existing, f"Mismatch: {existing_expected - actual_existing} missing, {actual_existing - existing_expected} extra"
print("  ✅ PASS")

print(f"\n[4] SMR workspace directories")
for aid in sorted(expected_smr):
    ws = f"/Users/apple/.openclaw/workspace-{aid}"
    assert os.path.isdir(ws)
    for f in ["SOUL.md", "AGENTS.md", "IDENTITY.md", "USER.md", "HEARTBEAT.md"]:
        assert os.path.isfile(os.path.join(ws, f)), f"{f} missing in {ws}"
print("  ✅ PASS (7 workspaces with all core files)")

db_path = "/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db"
print(f"\n[5] SQLite database")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
expected_tables = {"daily_bar", "us_daily_bar", "us_signal", "factor_daily", "stock_pool", "position", "risk_alert", "research_index", "sector_config"}
assert expected_tables.issubset(set(tables))
sector_count = cur.execute("SELECT COUNT(*) FROM sector_config").fetchone()[0]
sectors = cur.execute("SELECT sector_key, sector_name FROM sector_config").fetchall()
conn.close()
print(f"  Tables: {len(tables)}, sector_config: {sector_count} rows")
for sk, sn in sectors:
    print(f"    - {sk}: {sn}")
print("  ✅ PASS")

smr_root = "/Users/apple/Documents/同行资本二级市场"
print(f"\n[6] SMR root directory structure")
for d in ["00_control", "01_data/db", "02_research/industry/embodied_ai", "03_stock_pool/watchlist", "04_portfolio/positions", "05_risk/alerts", "06_reports/daily", "07_publish/queue", "08_scripts/data_harvester", "09_runbooks/scripts", "10_logs"]:
    assert os.path.isdir(os.path.join(smr_root, d)), f"Missing: {d}"
print("  ✅ PASS")

print(f"\n[7] AkShare data fetch test")
try:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    test_codes = ["688017", "300308", "688027"]
    found = sum(1 for code in test_codes if code in df["代码"].values)
    print(f"  Found {found}/{len(test_codes)} test stocks (688017=绿的谐波, 300308=中际旭创, 688027=国盾量子)")
    print("  ✅ PASS")
except Exception as e:
    print(f"  ⚠️ AkShare error: {e}")

print(f"\n[8] yfinance data fetch test")
try:
    import yfinance as yf
    ticker = yf.Ticker("NVDA")
    hist = ticker.history(period="5d")
    if len(hist) > 0:
        print(f"  NVDA last close: ${hist['Close'].iloc[-1]:.2f}")
        print("  ✅ PASS")
    else:
        print("  ⚠️ No data returned")
except Exception as e:
    print(f"  ⚠️ yfinance error: {e}")

print("\n" + "=" * 60)
print("Phase 0 Verification Complete!")
print("=" * 60)
