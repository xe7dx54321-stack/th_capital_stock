#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_cannot_conclude_guard import build_guard_report


def build(conn, ticker):
    return build_guard_report(ticker)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['cannot_conclude_guard']
        print(f"# Cannot-Conclude Guard Report")
        print(f"\n- Claims checked: {d['claims_checked']}")
        print(f"- Violations: {d['violations']}")
        print(f"- Guard status: {d['guard_status']}")
        print(f"\n## Blocked Claim Examples")
        for ex in d['blocked_claim_examples']:
            print(f"\n### Forbidden: {ex['forbidden_claim']}")
            print(f"- Allowed rewrite: {ex['allowed_rewrite']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
