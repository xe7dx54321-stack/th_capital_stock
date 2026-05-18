#!/usr/bin/env python3
"""Phase 0-6: Verification tests for SMR infrastructure."""

import json
import os
import sqlite3

print("=" * 60)
print("SMR Phase 0 Verification Tests")
print("=" * 60)

# Test 1: openclaw.json has 7 SMR agents
print("\n[1] Checking openclaw.json for SMR agents...")
with open("/Users/apple/.openclaw/openclaw.json", "r", encoding="utf-8") as f:
    config = json.load(f)

agent_ids = [a["id"] for a in config["agents"]["list"]]
smr_ids = [aid for aid in agent_ids if aid.startswith("smr-")]
expected_smr = {"smr-lead", "smr-researcher", "smr-analyst", "smr-advisor", "smr-portfolio-mgr", "smr-risk-controller", "smr-brief-writer"}
assert set(smr_ids) == expected_smr, f"SMR agents mismatch: {set(smr_ids)} vs {expected_smr}"
print(f"  ✅ 7 SMR agents found: {sorted(smr_ids)}")

# Test 2: agentToAgent.allow includes SMR agents
print("\n[2] Checking agentToAgent.allow for SMR agents...")
allow_list = config["tools"]["agentToAgent"]["allow"]
for aid in expected_smr:
    assert aid in allow_list, f"{aid} not in agentToAgent.allow"
print(f"  ✅ All 7 SMR agents in agentToAgent.allow")

# Test 3: Existing agents unchanged
print("\n[3] Checking existing agents are unchanged...")
existing_ids = {"lead", "knowledge-curator", "thesis-architect", "opportunity-scout", "red-team", "ic-ops", "signal-harvester", "market-scout", "topic-planner", "content-writer", "redteam-reviewer", "publish-ops", "content-analyst", "market-editor"}
actual_existing = agent_ids - expected_smr
# Note: actual_existing is a list, convert to set
actual_existing_set = set(agent_ids) - expected_smr
assert existing_ids == actual_existing_set, f"Existing agents changed! {existing_ids} vs {actual_existing_set}"
print(f"  ✅ All 14 existing agents unchanged")

# Test 4: Workspace directories exist
print("\n[4] Checking SMR workspace directories...")
for aid in sorted(expected_smr):
    ws = f"/Users/apple/.openclaw/workspace-{aid}"
    assert os.path.isdir(ws), f"Workspace missing: {ws}"
    soul = os.path.join(ws, "SOUL.md")
    agents_md = os.path.join(ws, "AGENTS.md")
    identity = os.path.join(ws, "IDENTITY.md")
    assert os.path.isfile(soul), f"SOUL.md missing in {ws}"
    assert os.path.isfile(agents_md), f"AGENTS.md missing in {ws}"
    assert os.path.isfile(identity), f"IDENTITY.md missing in {ws}"
print(f"  ✅ All 7 workspaces with core files")

# Test 5: SQLite database
print("\n[5] Checking SQLite database...")
db_path = "/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db"
assert os.path.isfile(db_path), f"Database missing: {db_path}"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
expected_tables = {"daily_bar", "us_daily_bar", "us_signal", "factor_daily", "stock_pool", "position", "risk_alert", "research_index", "sector_config"}
assert expected_tables.issubset(set(tables)), f"Tables missing: {expected_tables - set(tables)}"
sector_count = cur.execute("SELECT COUNT(*) FROM sector_config").fetchone()[0]
assert sector_count == 5, f"sector_config has {sector_count} rows, expected 5"
conn.close()
print(f"  ✅ Database with {len(tables)} tables, sector_config has {sector_count} rows")

# Test 6: SMR root directory structure
print("\n[6] Checking SMR root directory structure...")
smr_root = "/Users/apple/Documents/同行资本二级市场"
expected_dirs = ["00_control", "01_data/db", "02_research/industry/embodied_ai", "03_stock_pool/watchlist", "04_portfolio/positions", "05_risk/alerts", "06_reports/daily", "07_publish/queue", "08_scripts/data_harvester", "09_runbooks/scripts", "10_logs"]
for d in expected_dirs:
    assert os.path.isdir(os.path.join(smr_root, d)), f"Directory missing: {d}"
print(f"  ✅ All key directories exist")

# Test 7: AkShare can fetch data
print("\n[7] Testing AkShare data fetch...")
try:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    test_codes = ["688017", "300308", "688027"]
    found = 0
    for code in test_codes:
        if code in df["代码"].values:
            found += 1
    print(f"  ✅ AkShare working, found {found}/{len(test_codes)} test stocks in A-share data")
except Exception as e:
    print(f"  ⚠️ AkShare test failed: {e}")

# Test 8: yfinance can fetch US data
print("\n[8] Testing yfinance data fetch...")
try:
    import yfinance as yf
    ticker = yf.Ticker("NVDA")
    hist = ticker.history(period="5d")
    if len(hist) > 0:
        print(f"  ✅ yfinance working, NVDA last close: ${hist['Close'].iloc[-1]:.2f}")
    else:
        print(f"  ⚠️ yfinance returned empty data for NVDA")
except Exception as e:
    print(f"  ⚠️ yfinance test failed: {e}")

print("\n" + "=" * 60)
print("Phase 0 Verification Complete!")
print("=" * 60)
