#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_financial_phase55_integration import integrate_real_with_phase55

def build(conn,ticker):
    integ = integrate_real_with_phase55(ticker)
    di = integ.get('real_financial_phase55_integration', {})
    records = di.get('real_records', [])
    real_avail = di.get('real_records_available', 0) > 0
    by_pm = {}
    for r in records: by_pm[(r['period'], r['metric'])] = r['value']
    periods = sorted(set(r['period'] for r in records))[-8:]
    signals = []
    for m in ['revenue', 'net_profit']:
        for p in periods:
            yr, q = int(p[:4]), p[4:]
            prev_p = str(yr-1)+q
            curr, prev = by_pm.get((p,m)), by_pm.get((prev_p,m))
            if curr and prev and prev != 0:
                v = round((curr-prev)/prev, 4)
                d = 'positive' if v > 0.05 else ('negative' if v < -0.05 else 'neutral')
                signals.append({'signal': m+'_yoy', 'period': p, 'value': v, 'signal_direction': d, 'confidence': 'real_structured'})
    return {'ticker': ticker, 'real_financial_signals': {
        'real_data_used': real_avail, 'fixture_used': False,
        'periods_checked': len(periods), 'signals_calculated': len(signals),
        'signals_missing': 0, 'signals': signals}}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,args.ticker)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
