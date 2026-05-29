#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_watchlist_financial_delta_detector import detect_watchlist_financial_delta

def build(conn, ticker): return detect_watchlist_financial_delta(ticker)
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None, args.ticker)
    if args.markdown:
        d = r['watchlist_financial_delta']
        print(f"# {args.ticker} Financial Delta")
        print(f"\n- Variables: {d['variables_checked']}")
        print(f"- Strengthened: {d['variables_strengthened']}, Weakened: {d['variables_weakened']}")
        print(f"- Unchanged: {d['variables_unchanged']}, Unjudgeable: {d['variables_unjudgeable']}")
        print(f"- Summary: {d['delta_summary']}")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
