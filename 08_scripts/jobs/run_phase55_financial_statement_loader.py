#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_statement_loader import load_financial_statements

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--fixture-only',action='store_true')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    if args.dry_run:
        mode = 'dry-run'
    elif args.execute:
        mode = 'execute'
    elif args.fixture_only:
        mode = 'fixture-only'
    else:
        mode = 'dry-run'
    r = load_financial_statements(args.ticker, mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
