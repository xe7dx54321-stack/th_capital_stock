import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase84_daily_run_state import create_run_state,make_ticker_result
def build():
    s=create_run_state("execute");tickers=[("300308.SZ","CN_A",3,1,0,2,0),("688041.SH","CN_A",2,1,0,1,0),("002230.SZ","CN_A",1,0,0,1,0),("09988.HK","HK",2,1,0,1,0),("00700.HK","HK",2,1,0,1,0),("NVDA","US",5,2,0,3,0),("AVGO","US",1,0,0,1,0),("300394.SZ","CN_A",0,0,0,0,0)]
    for t,m,sig,st,w,uc,an in tickers:
        blocked=t=="300394.SZ";s["ticker_results"].append(make_ticker_result(t,m,"ok" if not blocked else "blocked","blocked" if blocked else "covered",sig,st,w,uc,an,"cninfo_org_id_missing_or_known_url_not_usable" if blocked else ""))
    s["signal_summary"]={"signals_loaded":sum(tr["signals_checked"] for tr in s["ticker_results"]),"strengthened":5,"weakened":0,"unchanged":10,"anomaly":0}
    s["board_summary"]={"strengthened":3,"weakened":0,"unchanged":4,"anomaly":0,"blocked":1}
    s["brief_quality_status"]="pass"
    return s
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
