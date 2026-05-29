#!/usr/bin/env python3
"""Phase 67 CNINFO pagination query job."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_pagination_query_engine import query_paginated
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--max-pages",type=int,default=5);p.add_argument("--page-size",type=int,default=30);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="execute" if getattr(a,"execute",False) else "dry_run";skip=getattr(a,"skip_network",False)
    r=query_paginated(a.ticker,a.max_pages,a.page_size,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
