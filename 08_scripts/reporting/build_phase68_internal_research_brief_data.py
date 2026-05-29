#!/usr/bin/env python3
'''Phase 68 internal research brief data builder report.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_internal_research_brief_data_builder import build_brief_data
from smr_evidence_claim_linkage_memory import build_claim_linkage
from smr_claim_state_memory import build_claim_state
from smr_phase68_evidence_loader import load_phase67b_evidence

def build(t='300308.SZ'):
    ev = load_phase67b_evidence()
    cl = build_claim_linkage(ev)
    cs = build_claim_state(cl['rows'])
    bd = build_brief_data(t, '中际旭创', 'AI光模块/光通信', ev, cl, cs)
    return {'ticker': t, 'internal_research_brief_data': bd}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build(a.ticker)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
