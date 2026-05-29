#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_quoted_span_validator import validate_quoted_spans
def build(conn,t=None): return validate_quoted_spans(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_quoted_span_validation']
        print(f"# Real Quoted Span Validation\n- Ticker: {r['ticker']}")
        print(f"- Checked: {d['spans_checked']} | Passed: {d['spans_passed']} | Review: {d['spans_review_required']} | Rejected: {d['spans_rejected']}")
        for s in d['rows'][:5]:
            print(f"  - {s['span_id']}: {s['validation_status']} ({s['business_variable']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
