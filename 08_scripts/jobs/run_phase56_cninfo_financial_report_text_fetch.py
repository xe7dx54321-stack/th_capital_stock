#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_cninfo_financial_report_text_adapter import fetch_cninfo_financial_report_text

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--skip-network',action='store_true')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    mode = 'skip-network' if args.__dict__.get('skip_network') else ('execute' if args.execute else 'dry-run')
    r = fetch_cninfo_financial_report_text(args.ticker, mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
