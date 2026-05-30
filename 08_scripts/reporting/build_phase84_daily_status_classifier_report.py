import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase84_daily_status_classifier import build_classification
def build():
    trs=[{"ticker":"NVDA","market":"US","strengthened_count":2,"weakened_count":0,"unchanged_count":3,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"688041.SH","market":"CN_A","strengthened_count":1,"weakened_count":0,"unchanged_count":1,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"300308.SZ","market":"CN_A","strengthened_count":1,"weakened_count":0,"unchanged_count":2,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"002230.SZ","market":"CN_A","strengthened_count":0,"weakened_count":0,"unchanged_count":1,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"09988.HK","market":"HK","strengthened_count":0,"weakened_count":0,"unchanged_count":2,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"00700.HK","market":"HK","strengthened_count":1,"weakened_count":0,"unchanged_count":1,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"AVGO","market":"US","strengthened_count":0,"weakened_count":0,"unchanged_count":1,"anomaly_count":0,"coverage_status":"covered","blocker":""},{"ticker":"300394.SZ","market":"CN_A","strengthened_count":0,"weakened_count":0,"unchanged_count":0,"anomaly_count":0,"coverage_status":"blocked","blocker":"cninfo_org_id_missing"}]
    return build_classification(trs)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
