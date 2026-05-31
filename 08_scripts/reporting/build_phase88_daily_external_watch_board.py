import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase88_daily_watch_board import build_daily_external_watch_board
def build():return build_daily_external_watch_board()
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
