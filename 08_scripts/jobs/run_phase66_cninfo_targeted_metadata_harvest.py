#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--max-metadata",type=int,default=50);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="dry-run" if getattr(a,"dry_run",False) else "execute";skip=getattr(a,"skip_network",False)
    r=harvest_targeted_metadata(a.ticker,a.max_metadata,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
