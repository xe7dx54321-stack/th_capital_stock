import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase85_valuation_daily_integration import integrate_signals_valuation
def build():
    signals=[{"ticker":"NVDA","market":"US","metric_name":"revenue","delta_status":"strengthened","cannot_conclude":["customer_share"]},{"ticker":"300308.SZ","market":"CN_A","metric_name":"revenue","delta_status":"strengthened","cannot_conclude":["customer_share"]},{"ticker":"09988.HK","market":"HK","metric_name":"revenue","delta_status":"unchanged","cannot_conclude":["customer_share"]}]
    bands=[{"ticker":"NVDA","band":"high","reason":"valuation_metrics_available"},{"ticker":"300308.SZ","band":"neutral","reason":"valuation_metrics_available"},{"ticker":"09988.HK","band":"low","reason":"valuation_metrics_available"}]
    return integrate_signals_valuation(signals,bands)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
