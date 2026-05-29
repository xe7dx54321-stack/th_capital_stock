#!/usr/bin/env python3
"""Phase 62: CNINFO Metadata Fetch Job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_cninfo_business_metadata_connector import fetch_cninfo_metadata

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--execute',action='store_true')
    p.add_argument('--skip-network',action='store_true'); p.add_argument('--json',action='store_true')
    a=p.parse_args()
    mode = 'dry-run' if a.dry_run else ('skip-network' if a.skip_network else 'execute')
    r = fetch_cninfo_metadata(a.ticker, mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
