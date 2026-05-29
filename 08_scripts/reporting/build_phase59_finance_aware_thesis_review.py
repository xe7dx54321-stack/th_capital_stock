#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review

def build(conn, ticker): return run_finance_aware_thesis_review(ticker)
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    args = p.parse_args(); r = build(None, args.ticker)
    if args.markdown:
        d = r['finance_aware_thesis_review']
        print(f"# Finance-Aware Thesis Review")
        print(f"\n- Overall: {d['overall_review']}")
        print(f"- Strengthened: {d['claims_strengthened']}, Unconfirmed: {d['claims_unconfirmed']}")
        for row in d['rows']:
            print(f"\n## {row['claim']}: {row['review_result']}")
            print(f"- {row['limitation']}")
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
