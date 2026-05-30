import json
from pathlib import Path
CFG=Path(__file__).resolve().parents[2]/"config"/"phase84_scheduled_daily_monitoring.json"
def load_config():
    with open(CFG,"r",encoding="utf-8-sig") as f:return json.load(f)
def validate_config():
    c=load_config()
    checks={"strategy_ok":"daily_monitoring" in c["strategy"],"universe_8":len(c["universe"]["tickers"])==8,"covered_7":len(c["universe"]["covered_tickers"])==7,"blocked_1":len(c["universe"]["blocked_tickers"])==1,"has_300394_blocked":"300394.SZ" in c["universe"]["blocked_tickers"],"cron_disabled":c["schedule"]["cron_enabled"]==False,"valuation_disabled":c["safety"]["valuation_enabled"]==False,"portfolio_disabled":c["safety"]["portfolio_construction_enabled"]==False,"history_enabled":c["history"]["enabled"]==True,"mock_ok":c["safety"]["mock_allowed"]==False}
    return {"all_pass":all(checks.values()),"checks":checks}
