#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_business_source_coverage_audit import audit_coverage
def build(conn,t=None): return audit_coverage(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_source_coverage_audit']
        print(f"# Real Business Source Coverage Audit\n- Ticker: {r['ticker']}")
        print(f"- Variables covered/not: {d['variables_with_real_text_coverage']}/{d['variables_without_real_text_coverage']}")
        print(f"- Status: {d['coverage_status']}")
        for c in d['coverage_rows']:
            print(f"  - {c['business_variable']}: {c['coverage_status']} (sources: {c['real_text_sources']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
