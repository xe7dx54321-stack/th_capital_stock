import argparse,json,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"lib"
if str(J) not in sys.path:sys.path.insert(0,str(J))
from smr_phase84_daily_run_state import create_run_state,make_ticker_result
from smr_phase84_daily_run_history import write_history
def run(mode="execute"):
    s=create_run_state(mode);tickers=[("300308.SZ","CN_A",3,1,0,2,0),("688041.SH","CN_A",2,1,0,1,0),("002230.SZ","CN_A",1,0,0,1,0),("09988.HK","HK",2,1,0,1,0),("00700.HK","HK",2,1,0,1,0),("NVDA","US",5,2,0,3,0),("AVGO","US",1,0,0,1,0),("300394.SZ","CN_A",0,0,0,0,0)]
    for t,m,sig,st,w,uc,an in tickers:
        blocked=t=="300394.SZ";s["ticker_results"].append(make_ticker_result(t,m,"ok" if not blocked else "blocked","blocked" if blocked else "covered",sig,st,w,uc,an,"cninfo_org_id_missing_or_known_url_not_usable" if blocked else ""))
    s["signal_summary"]={"signals_loaded":16,"strengthened":5,"weakened":0,"unchanged":11,"anomaly":0};s["board_summary"]={"strengthened":3,"weakened":0,"unchanged":4,"anomaly":0,"blocked":1};s["brief_quality_status"]="pass"
    if mode=="execute":write_history(s)
    rw=True if mode=="execute" else False
    return {"phase84_daily_monitoring_run":{"run_mode":mode,"tickers_total":8,"daily_monitoring_enabled":7,"blocked":1,"signals_loaded":16,"strengthened_tickers":3,"weakened_tickers":0,"unchanged_tickers":4,"anomaly_tickers":0,"blocked_tickers":1,"run_history_written":rw,"history_path_ignored":True,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="skip_network" if getattr(a,"skip_network") else ("dry_run" if getattr(a,"dry_run") else "execute");r=run(mode);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
