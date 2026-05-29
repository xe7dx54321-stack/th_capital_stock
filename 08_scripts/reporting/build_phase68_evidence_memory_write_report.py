#!/usr/bin/env python3
'''Phase 68 evidence memory write report.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
J = Path(__file__).resolve().parents[1] / 'jobs'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(J) not in sys.path: sys.path.insert(0, str(J))
from smr_evidence_memory_writer import write_evidence_memory
from smr_phase68_evidence_loader import load_phase67b_evidence

def build(t='300308.SZ'):
    ev = load_phase67b_evidence()
    r = write_evidence_memory(t, ev, company_name='中际旭创', industry='AI光模块/光通信', dry_run=False)
    return {'ticker': t, 'evidence_memory_write_report': r}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build(a.ticker)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
