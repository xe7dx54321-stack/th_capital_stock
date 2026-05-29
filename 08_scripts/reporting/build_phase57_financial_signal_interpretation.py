#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_signal_interpretation import interpret_financial_signals


def build(conn, ticker):
    return interpret_financial_signals(ticker)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['financial_signal_interpretation']
        print(f"# {args.ticker} Financial Signal Interpretation")
        print(f"\n## Overall: {d['overall_interpretation']}")
        print(f"\n- Positive: {d['positive_count']}, Negative: {d['negative_count']}")
        print(f"\n## Observations ({d['latest_period']})")
        for o in d['observations']:
            print(f"\n### {o['label']}")
            print(f"- Value: {o['value']}")
            print(f"- Direction: {o['direction']}")
            print(f"- {o['implication']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
