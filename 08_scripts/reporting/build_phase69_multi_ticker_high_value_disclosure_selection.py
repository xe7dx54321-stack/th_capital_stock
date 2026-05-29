#!/usr/bin/env python3
"""High-value disclosure selection report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_multi_ticker_high_value_disclosure_selector import select_multi_ticker_high_value

def build():
    r = select_multi_ticker_high_value(max_pdfs_per_ticker=10)
    return {'multi_ticker_high_value_disclosure_selection': r}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--max-pdfs-per-ticker', type=int, default=10); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
