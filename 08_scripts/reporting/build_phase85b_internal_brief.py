import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase85b_source_exhaustion_report import build_source_exhaustion_report
def build():
    r=build_source_exhaustion_report();d=r["phase85b_source_exhaustion_report"]
    return {"phase85b_internal_brief":{"format":"markdown","sections":5,"tickers_checked":d["tickers_checked"],"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
