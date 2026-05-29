#!/usr/bin/env python3
'''Phase 68 internal brief quality lint.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
R = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))
from smr_internal_brief_quality_lint import lint_brief

def build(t='300308.SZ'):
    from build_phase68_internal_research_brief import build as build_brief
    br = build_brief(t)
    md = br.get('phase68_internal_research_brief', {}).get('markdown', '')
    lt = lint_brief(md)
    return {'ticker': t, 'internal_brief_quality_lint': lt}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build(a.ticker)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
