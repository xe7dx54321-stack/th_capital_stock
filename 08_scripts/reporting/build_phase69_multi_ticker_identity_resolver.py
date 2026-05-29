#!/usr/bin/env python3
'''Phase 69 identity resolver report.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_multi_ticker_disclosure_identity_resolver import resolve_multi_ticker_identities
    r = resolve_multi_ticker_identities()
    return {'multi_ticker_identity_resolver': r}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    ri = r['multi_ticker_identity_resolver']
    if a.markdown: print('# Identity Resolver\n\nResolved: {}\nMissing: {}'.format(ri['identity_resolved'], ri['identity_missing']))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
