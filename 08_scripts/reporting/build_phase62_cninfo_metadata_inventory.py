#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_cninfo_business_metadata_connector import fetch_cninfo_metadata
def build(conn,t=None): return fetch_cninfo_metadata(t or '300308.SZ', 'execute')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['cninfo_metadata_inventory']
        print(f"# CNINFO Metadata Inventory\n- Ticker: {r['ticker']}")
        print(f"- Sources: {d['sources_found']} | Network: {d['network_used']} | Mode: {d['mode']}")
        for row in d['rows'][:10]:
            print(f"  - {row['source_id']}: {row['title'][:40]} ({row['source_type']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
