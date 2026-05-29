#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_chinese_business_source_registry import build_registry_report
def build(c,t=None): return build_registry_report()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None)
    if a.markdown:
        print(f"# Chinese Business Source Registry\n- Sources: {r['sources_count']}")
        for row in r['rows']:
            print(f"- {row['source_id']} [{row['priority']}]: {row['allowed_usage']} (network: {row['requires_network']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
