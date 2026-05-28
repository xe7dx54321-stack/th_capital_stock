#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

from smr_research_brief_depth_lint import build_depth_lint
from smr_investment_logic_brief_builder import build_investment_logic_brief

def build(conn,ticker):
    brief = build_investment_logic_brief(ticker)
    ib = brief['investment_logic_brief']
    # Build full text from user-visible sections
    parts = []
    parts.append(ib.get('one_line_conclusion',''))
    parts.extend(ib.get('current_observations', []))
    parts.extend(ib.get('implications', []))
    parts.extend(ib.get('can_conclude', []))
    parts.extend(ib.get('cannot_conclude', []))
    parts.extend(ib.get('current_conclusion', []))
    full_text = ' '.join(parts)
    return build_depth_lint(full_text)

def _md(p):
    dl=p.get('research_brief_depth_lint',{})
    return '# Depth Lint\n- status: ' + str(dl.get('depth_status','')) + '\n- passed: ' + str(dl.get('checks_passed','')) + '\n- system_terms: ' + str(dl.get('system_status_terms_found',0))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,args.ticker)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
