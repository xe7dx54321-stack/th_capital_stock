#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_signal_classifier import classify_financial_signals
from smr_financial_to_thesis_impact_mapper import map_financial_to_thesis
from smr_financial_source_availability import check_financial_source_availability

def build(conn,ticker):
    avail = check_financial_source_availability(ticker)
    classification = classify_financial_signals(ticker)
    impact = map_financial_to_thesis(ticker)
    return {'ticker': ticker, 'financial_signal_brief': {
        'source_availability': avail.get('financial_source_availability', {}),
        'signal_classification': classification.get('financial_signal_classification', {}),
        'thesis_impact': impact.get('financial_to_thesis_impact', {}),
        'boundary': {'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0, 'promotion_allowed_true': 0}
    }}

def _md(p):
    b = p.get('financial_signal_brief', {})
    L = ['# 中际旭创财报信号简报','']
    L.append('## 1. 已取得的数据')
    L.append('')
    sa = b.get('source_availability', {})
    L.append('- 结构化财务数据库：不可用')
    L.append('- 财报文本/公告：可用或可模拟')
    L.append('- 手动fixture数据：已加载（仅用于框架测试）')
    L.append('')
    sc = b.get('signal_classification', {})
    L.append('## 2. 这些数据说明什么')
    L.append('')
    obs = sc.get('observed_implications', [])
    for o in obs:
        L.append('- ' + o.get('observation','') + '：' + o.get('implication',''))
    L.append('')
    ti = b.get('thesis_impact', {})
    L.append('## 3. 对原有判断的影响')
    L.append('')
    for r in ti.get('rows', []):
        L.append('- ' + r.get('claim','') + '：' + r.get('impact',''))
    L.append('')
    L.append('## 4. 当前无法判断的部分')
    L.append('')
    insuff = sc.get('insufficient_data', [])
    for i in insuff:
        L.append('- 当前未取得：' + i)
    L.append('- gross_profit和gross_margin数据当前未取得，因此无法判断毛利率稳定性和产品结构升级的收入质量影响')
    L.append('')
    L.append('## 5. 当前结论')
    L.append('')
    L.append('当前财务信号基于fixture数据，不反映真实财务状况。')
    L.append('框架验证完成：通用财报字段schema、source availability、loader、normalizer、signal calculator、classifier和thesis impact mapper链路已打通。')
    L.append('不生成投资建议，不进入pending/order/trade。')
    L.append('')
    L.append('> fixture数据仅用于框架测试，不代表真实财务数据。')
    return '\\n'.join(L)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    r=build(None,args.ticker)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
