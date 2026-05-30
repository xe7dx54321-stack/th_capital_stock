import json
from pathlib import Path
CFG=Path(__file__).resolve().parents[2]/"config"/"phase83_hk_us_financial_adapters.json"
def load_config():
    with open(CFG,"r",encoding="utf-8-sig") as f:return json.load(f)
def validate_config():
    c=load_config()
    checks={"strategy_ok":"hk_us" in c["strategy"],"has_09988":any(t["ticker"]=="09988.HK" for t in c["target_tickers"]),"has_00700":any(t["ticker"]=="00700.HK" for t in c["target_tickers"]),"has_NVDA":any(t["ticker"]=="NVDA" for t in c["target_tickers"]),"has_AVGO":any(t["ticker"]=="AVGO" for t in c["target_tickers"]),"hk_us_separated":c["unit_policy"]["HK"]!=c["unit_policy"]["US"],"mock_ok":c["safety"]["mock_allowed"]==False}
    return {"all_pass":all(checks.values()),"checks":checks}
