#!/usr/bin/env python3
"""Multi-ticker metadata inventory report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_multi_ticker_disclosure_metadata_fetcher import fetch_multi_ticker_metadata

def build():
    r = fetch_multi_ticker_metadata(dry_run=True)
    return {'multi_ticker_metadata_inventory': r}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
