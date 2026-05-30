import json
from pathlib import Path
CFG=Path(__file__).resolve().parents[2]/"config"/"phase81_time_series_watchlist_monitoring.json"
def load_config():
    with open(CFG,"r",encoding="utf-8-sig") as f:return json.load(f)
def validate_config():
    c=load_config()
    checks={"strategy_ok":c["strategy"]=="time_series_signals_into_watchlist_continuous_monitoring","target_ok":c["target_ticker"]=="688041.SH","revenue_covered":"revenue" in c["signals"],"gm_covered":"gross_margin" in c["signals"],"rd_covered":"R&D_expense" in c["signals"],"np_covered":"net_profit" in c["signals"],"ocf_covered":"operating_cash_flow" in c["signals"],"mock_ok":c["safety"]["mock_allowed"]==False,"fixture_ok":c["safety"]["fixture_allowed"]==False,"raw_ok":c["safety"]["raw_save_allowed"]==False}
    return {"all_pass":all(checks.values()),"checks":checks}
