import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase86_integration import build_integration
def build():
    r=build_integration();d=r["phase86_integration"]
    return {"summary":{"tickers_total":d["tickers_total"],"pricing_available":d["pricing_available"],"valuation_available":d["valuation_available"],"expectation_available":d["expectation_available"],"full_integration":d["full_integration"],"target_price_output_count":0,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
