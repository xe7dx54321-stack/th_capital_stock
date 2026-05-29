#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_finance_aware_watchlist_decision import make_finance_aware_watchlist_decision

def build(conn, ticker): return make_finance_aware_watchlist_decision(ticker)
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None, args.ticker)
    if args.markdown:
        d = r['finance_aware_watchlist_decision']
        print(f"# Watchlist Decision")
        print(f"\n- Decision: {d['decision']}")
        print(f"- Confidence: {d['decision_confidence']}")
        for reason in d['decision_reason']: print(f"- {reason}")
        print(f"\n- Forbidden: {', '.join(d['forbidden_actions'])}")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
