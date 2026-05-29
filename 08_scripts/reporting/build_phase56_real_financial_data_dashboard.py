#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from smr_real_financial_phase55_integration import integrate_real_with_phase55
from smr_real_financial_data_quality import check_real_data_quality

def build(conn,ticker):
    integ = integrate_real_with_phase55(ticker)
    quality = check_real_data_quality(ticker)
    di = integ.get('real_financial_phase55_integration', {})
    dq = quality.get('real_financial_data_quality', {})
    real_avail = di.get('real_records_available', 0) > 0
    return {'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'summary': {
        'ticker': '300308.SZ',
        'real_structured_available': real_avail,
        'real_records_loaded': di.get('real_records_available', 0),
        'periods_loaded': dq.get('periods_covered', 0),
        'metrics_loaded': dq.get('metrics_covered', 0),
        'fixture_used': False,
        'fixture_contamination': dq.get('fixture_contamination', False),
        'quality_status': dq.get('quality_status', ''),
        'phase55_integration_ready': di.get('phase55_normalizer_ready', False),
        'pending_created': 0,
        'paper_order_created': 0,
        'real_trade_created': 0}}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,args.ticker)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
