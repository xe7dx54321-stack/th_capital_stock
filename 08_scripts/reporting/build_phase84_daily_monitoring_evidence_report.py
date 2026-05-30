import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase84_daily_monitoring_evidence import build as build_ev
def build():
    cl=[{"ticker":"NVDA","classification":"strengthened"},{"ticker":"688041.SH","classification":"strengthened"},{"ticker":"300308.SZ","classification":"strengthened"},{"ticker":"002230.SZ","classification":"unchanged"},{"ticker":"09988.HK","classification":"unchanged"},{"ticker":"00700.HK","classification":"unchanged"},{"ticker":"AVGO","classification":"unchanged"},{"ticker":"300394.SZ","classification":"blocked"}]
    return build_ev(cl)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
