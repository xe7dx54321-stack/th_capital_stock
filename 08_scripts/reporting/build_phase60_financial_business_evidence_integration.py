#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_business_evidence_integrator import integrate_financial_business_evidence
def build(c,t=None): return integrate_financial_business_evidence(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        for k,v in r.items():
            if k!=a.ticker and isinstance(v,dict):
                print(f"# {k}"); print(json.dumps(v,ensure_ascii=False,indent=2)[:2000])
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
