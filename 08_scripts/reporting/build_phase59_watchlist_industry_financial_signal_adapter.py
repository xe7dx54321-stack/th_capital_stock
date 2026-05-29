#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_watchlist_industry_financial_signal_adapter import build_watchlist_industry_financial_signal_adapter

def build(conn, ticker): return build_watchlist_industry_financial_signal_adapter(ticker)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None, args.ticker)
    if args.markdown:
        d = r['watchlist_industry_financial_signal_adapter']
        print(f"# {args.ticker} Watchlist Financial Signal Adapter")
        print(f"\n- Real data: {d['real_financial_data_used']}")
        print(f"- Variables loaded: {d['industry_variables_loaded']}")
        print(f"- Supported: {d['industry_variables_supported']}")
        print(f"- Partially supported: {d['industry_variables_partially_supported']}")
        print(f"- Unconfirmed: {d['industry_variables_unconfirmed']}")
        print(f"- Guard: {d['cannot_conclude_guard_status']}")
        print(f"\n## Key Observations")
        for o in d['key_observations']: print(f"- {o}")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
