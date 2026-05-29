#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_cninfo_real_network_fetch_validator import validate_cninfo_network
def build(conn,t=None): return validate_cninfo_network(t or '300308.SZ', 'execute')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    p.add_argument('--skip-network',action='store_true')
    a=p.parse_args(); mode = 'skip-network' if a.skip_network else 'execute'
    r=validate_cninfo_network(a.ticker, mode)
    if a.markdown:
        d=r['cninfo_real_network_validation']
        print(f"# CNINFO Network Validation\n- Ticker: {r['ticker']} | Mode: {d['mode']}")
        print(f"- Network: {d['network_available']} | Sources: {d['metadata_sources_found']} | Status: {d['status']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
