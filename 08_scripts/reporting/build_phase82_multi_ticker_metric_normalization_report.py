import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
def build():from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_metric_normalizer import normalize_metrics;m=load_multi_ticker_metrics();return normalize_metrics(m)
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
