#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables


def build(conn, ticker):
    return map_signals_to_industry_variables(ticker)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['financial_signal_to_industry_variable_map']
        print(f"# {args.ticker} Financial Signal to Industry Variable Map")
        print(f"\n- Industry: {r['industry']}")
        print(f"- Signals checked: {d['signals_checked']}")
        print(f"- Latest period: {d['latest_period']}")
        print(f"- Variables mapped: {d['industry_variables_mapped']}")
        for row in d['rows']:
            print(f"\n## {row['industry_variable']}")
            print(f"- Status: {row['variable_status']}")
            print(f"- {row['interpretation']}")
            print(f"- Cannot conclude: {', '.join(row['cannot_conclude'][:3])}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
