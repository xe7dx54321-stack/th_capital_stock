import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase84_previous_run_comparison import compare
def build():
    return compare({"ticker_results":[{"ticker":"NVDA","run_status":"ok","strengthened_count":2,"weakened_count":0,"anomaly_count":0,"blocker":""}]})
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args()
    print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
