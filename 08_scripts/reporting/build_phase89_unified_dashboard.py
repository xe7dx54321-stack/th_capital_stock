import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase89_integration import build_unified_integration
def build():
    r=build_unified_integration();d=r["phase89_unified_integration"]
    return {"summary":{"tickers":d["tickers_total"],"full_coverage":d["full_coverage"],"partial":d["partial"],"degraded":d["degraded"],"blocked":d["blocked"],"source_health":d["source_health_overall"],"known_gaps":d["known_gaps"],"watch_only":True,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
