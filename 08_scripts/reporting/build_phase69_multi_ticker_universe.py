#!/usr/bin/env python3
'''Phase 69 multi-ticker universe report.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_multi_ticker_universe import load_universe

def build():
    u = load_universe()
    rows = [{'ticker': t['ticker'], 'company_name': t['company_name'], 'market': t['market'], 'board': t['board'], 'role': t['role'], 'industry_template': t['industry_template']} for t in u.get('tickers', [])]
    return {'tickers': rows, 'total': len(rows)}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    elif a.markdown: print('# Multi-ticker Universe\n\n' + '\n'.join(f'- {t["ticker"]}: {t["company_name"]}' for t in r['tickers']))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
