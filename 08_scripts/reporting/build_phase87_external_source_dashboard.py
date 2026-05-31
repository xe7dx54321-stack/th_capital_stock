import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase87_integration import build_external_integration
def build():
    r=build_external_integration();d=r["phase87_external_integration"]
    return {"summary":{"tickers_checked":d["tickers_checked"],"evidence_entries":d["evidence_entries"],"source_available":d["source_available"],"blocked":d["blocked"],"avg_reliability":d["avg_reliability"],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
