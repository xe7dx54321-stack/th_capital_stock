import json
from pathlib import Path
CFG=Path(__file__).resolve().parents[2]/"config"/"phase82_multi_ticker_financial_coverage.json"
def load_config():
    with open(CFG,"r",encoding="utf-8-sig") as f:return json.load(f)
def validate_config():
    c=load_config()
    checks={"strategy_ok":"multi_ticker" in c["strategy"],"universe_size":len(c["universe"])>=4,"has_300308":any(t["ticker"]=="300308.SZ" for t in c["universe"]),"has_688041":any(t["ticker"]=="688041.SH" for t in c["universe"]),"has_300394":any(t["ticker"]=="300394.SZ" for t in c["universe"]),"has_002230":any(t["ticker"]=="002230.SZ" for t in c["universe"]),"markets_present":len(set(t["market"] for t in c["universe"]))>=1,"mock_ok":c["safety"]["mock_allowed"]==False,"fixture_ok":c["safety"]["fixture_allowed"]==False,"raw_ok":c["safety"]["raw_save_allowed"]==False}
    return {"all_pass":all(checks.values()),"checks":checks}
