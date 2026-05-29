#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_irm_interactive_qa_connector import fetch_irm_qa

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true")
    p.add_argument("--max-sources",type=int,default=10)
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    mode="execute" if args.execute else ("dry-run" if getattr(args,"dry_run",False) else "execute")
    skip=getattr(args,"skip_network",False)
    result=fetch_irm_qa(args.ticker,args.max_sources,mode,skip_network=skip)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
