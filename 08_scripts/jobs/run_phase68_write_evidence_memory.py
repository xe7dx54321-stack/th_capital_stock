#!/usr/bin/env python3
'''Phase 68 write evidence memory job.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_evidence_memory_writer import write_evidence_memory
from smr_phase68_evidence_loader import load_phase67b_evidence

def run(t='300308.SZ', dry_run=False):
    ev = load_phase67b_evidence()
    r = write_evidence_memory(t, ev, company_name='中际旭创', industry='AI光模块/光通信', dry_run=dry_run)
    return {'ticker': t, 'evidence_memory_write_job': r}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--dry-run', action='store_true'); p.add_argument('--execute', action='store_true'); p.add_argument('--json', action='store_true')
    a = p.parse_args(); dry = getattr(a, 'dry_run', False)
    r = run(a.ticker, dry_run=dry)
    print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
