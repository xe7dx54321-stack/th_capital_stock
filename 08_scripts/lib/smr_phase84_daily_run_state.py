import json,datetime,uuid
from pathlib import Path
SCHEMA=Path(__file__).resolve().parents[2]/"config"/"phase84_daily_run_state_schema.json"
def load_schema():
    with open(SCHEMA,"r",encoding="utf-8-sig") as f:return json.load(f)
def create_run_state(mode="execute",universe_count=8,covered=7,blocked=1):
    now=datetime.datetime.now().isoformat()
    return {"run_id":f"phase84-{datetime.date.today().isoformat()}","run_date":datetime.date.today().isoformat(),"run_mode":mode,"started_at":now,"finished_at":now,"duration_seconds":0.1,"universe_count":universe_count,"covered_count":covered,"blocked_count":blocked,"ticker_results":[],"signal_summary":{"signals_loaded":0,"strengthened":0,"weakened":0,"unchanged":0,"anomaly":0},"board_summary":{"strengthened":0,"weakened":0,"unchanged":0,"anomaly":0,"blocked":0},"safety_summary":{"pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False},"brief_quality_status":"pending"}
def make_ticker_result(ticker,market,run_status="ok",coverage="covered",signals=0,strengthened=0,weakened=0,unchanged=0,anomaly=0,blocker=""):
    return {"ticker":ticker,"market":market,"run_status":run_status,"coverage_status":coverage,"signals_checked":signals,"strengthened_count":strengthened,"weakened_count":weakened,"unchanged_count":unchanged,"anomaly_count":anomaly,"blocker":blocker,"failure_reason":"","pending_created":0,"paper_order_created":0,"real_trade_created":0}
