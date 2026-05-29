#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_ai_optical_business_variable_schema import build_business_schema_report
def build(c,t=None): return build_business_schema_report()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None)
    if a.markdown:
        print(f"# Business Variable Schema\n- Variables: {r['variables_count']}\n- Forbidden: {r['forbidden_count']}")
        for v in r['variables']: print(f"\n## {v['variable']}\n- {v['description']}\n- Keywords: {v['keywords_count']}\n- Cannot-conclude: {v['cannot_conclude_count']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
