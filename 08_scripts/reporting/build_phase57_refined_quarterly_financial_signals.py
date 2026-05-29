#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def build(conn, ticker):
    result = calculate_refined_quarterly_signals(ticker)
    # Remove full all_signals list from display (too large)
    display = {k: v for k, v in result.items()}
    ds = display.get('refined_quarterly_financial_signals', {})
    ds.pop('all_signals', None)
    return display


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['refined_quarterly_financial_signals']
        print(f"# {args.ticker} Refined Quarterly Financial Signals")
        print(f"\n- Real data used: {d['real_data_used']}")
        print(f"- Fixture used: {d['fixture_used']}")
        print(f"- Single quarter used: {d['single_quarter_used']}")
        print(f"- Periods checked: {d['periods_checked']}")
        print(f"- Latest period: {d['latest_period']}")
        print(f"- Signals calculated: {d['signals_calculated']}")
        print(f"- Signals missing: {d['signals_missing']}")
        if d['latest_signals']:
            print(f"\n## Latest signals ({d['latest_period']})")
            for s in d['latest_signals']:
                print(f"- {s['signal']}: {s['value']} ({s['direction']})")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
