#!/usr/bin/env python3
"""Phase 69b 688041.SH real execute report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / 'jobs'
if str(J) not in sys.path: sys.path.insert(0, str(J))
def build():
    from run_phase69b_688041_real_execute import run
    r = run(mode='execute')
    return r
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
