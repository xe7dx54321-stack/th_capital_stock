#!/usr/bin/env python3
"""Phase 62: Controlled Chinese Text Fetch Job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_controlled_chinese_text_fetcher import fetch_controlled_chinese_texts

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--execute',action='store_true')
    p.add_argument('--skip-network',action='store_true'); p.add_argument('--max-sources',type=int,default=10)
    p.add_argument('--json',action='store_true')
    a=p.parse_args()
    mode = 'dry-run' if a.dry_run else ('skip-network' if a.skip_network else 'execute')
    r = fetch_controlled_chinese_texts(a.ticker, mode, a.max_sources)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
