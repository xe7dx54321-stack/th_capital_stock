import json
from pathlib import Path
CFG=Path(__file__).resolve().parents[2]/"config"/"phase85_valuation_integration.json"
def load_config():
    with open(CFG,"r",encoding="utf-8-sig") as f:return json.load(f)
def validate_config():
    c=load_config()
    checks={"strategy_ok":"valuation" in c["strategy"],"tickers_8":len(c["target_tickers"])==8,"has_300394_blocked":"300394.SZ" in c["known_blocked"],"bands_5":len(c["bands"])==5,"mock_ok":c["safety"]["mock_allowed"]==False,"target_price_disabled":c["safety"]["target_price_allowed"]==False,"position_sizing_disabled":c["safety"]["position_sizing_allowed"]==False}
    return {"all_pass":all(checks.values()),"checks":checks}
