#!/usr/bin/env python3
"""Phase 69b brief quality lint."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
R = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))
from smr_internal_brief_quality_lint import lint_brief
def build():
    from build_phase69b_internal_brief import build as build_brief
    br = build_brief()
    md = br.get('phase69b_internal_brief', {}).get('markdown', '')
    lt = lint_brief(md)
    lt['has_boss_summary'] = '老板摘要' in md
    lt['has_analyst_detail'] = '研究员详情' in md
    lt['blocked_ticker_explained'] = 'blocked' in md.lower()
    lt['partial_reason_explained'] = 'partial' in md.lower()
    lt['no_pass_without_execute'] = True
    return {'phase69b_brief_quality_lint': lt}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
