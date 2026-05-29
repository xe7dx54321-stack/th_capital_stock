#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_controlled_online_text_fetch_validator import validate_online_text_fetch
def build(conn,t=None): return validate_online_text_fetch(t or '300308.SZ', 'execute', 10)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    p.add_argument('--skip-network',action='store_true'); p.add_argument('--max-sources',type=int,default=10)
    a=p.parse_args(); mode = 'skip-network' if a.skip_network else 'execute'
    r=validate_online_text_fetch(a.ticker, mode, a.max_sources)
    if a.markdown:
        d=r['controlled_online_text_fetch_validation']
        print(f"# Online Text Fetch Validation\n- Ticker: {r['ticker']}")
        print(f"- Text OK: {d['text_ok']} | PDF: {d['pdf_text_ok']} | Meta: {d['metadata_only']} | Failed: {d['failed']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
