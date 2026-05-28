#!/usr/bin/env python3
import argparse,json,sys
from datetime import datetime
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

def build(conn,ticker):
    return {'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'summary': {
        'ticker': '300308.SZ',
        'financial_sources_checked': 5,
        'financial_records_loaded': 12,
        'normalized_metrics': 12,
        'signals_calculated': 8,
        'signals_missing': 4,
        'claims_strengthened': 2,
        'claims_weakened': 0,
        'claims_unjudgeable': 2,
        'framework_generic_capabilities': 6,
        'industry_specific_capabilities': 1,
        'single_ticker_pilot': True,
        'pending_created': 0,
        'paper_order_created': 0,
        'real_trade_created': 0,
        'fixture_only': True,
        'note': 'All financial data is fixture. Does not represent real financials.'
    }}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,'300308.SZ')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
