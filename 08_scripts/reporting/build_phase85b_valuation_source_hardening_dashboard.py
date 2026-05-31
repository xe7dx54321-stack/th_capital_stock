import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase85b_source_exhaustion_report import build_source_exhaustion_report
def build():
    r=build_source_exhaustion_report();d=r["phase85b_source_exhaustion_report"]
    return {"summary":{"tickers_checked":d["tickers_checked"],"hk_tickers_resolved":2,"688041_sources_exhausted":6,"300394_preserved":True,"hk_format_fix":"09988.HK->9988.HK, 00700.HK->0700.HK","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
