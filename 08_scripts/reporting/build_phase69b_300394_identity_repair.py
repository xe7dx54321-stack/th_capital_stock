#!/usr/bin/env python3
"""Phase 69b 300394.SZ identity repair report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
def build():
    r = attempt_identity_repair('300394.SZ')
    return {'ticker': '300394.SZ', 'phase69b_300394_identity_repair': r}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
