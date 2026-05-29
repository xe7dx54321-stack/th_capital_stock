#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_industry_financial_variable_interpretation import interpret_industry_financial_variables


def build(conn, ticker):
    return interpret_industry_financial_variables(ticker)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['industry_financial_variable_interpretation']
        print(f"# {args.ticker} Industry Financial Variable Interpretation")
        print(f"\n## Overall: {d['overall_interpretation']}")
        for o in d['observations']:
            print(f"\n### Observed: {o['observed_financial_fact']}")
            print(f"- Business implication: {o['business_implication']}")
            print(f"- Status: {o['judgment_status']}")
            print(f"- Cannot conclude: {o['cannot_conclude']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
