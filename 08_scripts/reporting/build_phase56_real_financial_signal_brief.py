#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_financial_phase55_integration import integrate_real_with_phase55
from smr_real_financial_data_quality import check_real_data_quality

def build(conn,ticker):
    integ = integrate_real_with_phase55(ticker)
    quality = check_real_data_quality(ticker)
    di = integ.get('real_financial_phase55_integration', {})
    dq = quality.get('real_financial_data_quality', {})
    real_avail = di.get('real_records_available', 0) > 0
    return {'ticker': ticker, 'real_financial_signal_brief': {
        'real_data_available': real_avail,
        'quality': dq,
        'integration': di,
        'boundary': {'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0}
    }}

def _md(p):
    b = p.get('real_financial_signal_brief', {})
    L = ['# 中际旭创真实财务信号简报','']
    dq = b.get('quality', {})
    L.append('## 1. 已取得的数据')
    L.append('')
    if b.get('real_data_available'):
        L.append('- 真实结构化财务数据已通过 akshare/sina 接口取得')
        L.append('- 数据质量：' + str(dq.get('quality_status','')))
        L.append('- 覆盖期间：' + str(dq.get('periods_covered', 0)))
    else:
        L.append('- 当前未取得真实结构化财务数据')
        L.append('- 本简报只能说明数据接入状态，不能形成真实财务判断')
    L.append('')
    L.append('## 2. 数据接入状态')
    L.append('')
    if b.get('real_data_available'):
        L.append('- 结构化财务 adapter：已接入 akshare/sina 真实数据')
    else:
        L.append('- 结构化财务 adapter：未取得真实数据')
    L.append('- CNINFO fallback：接口已建立，第一版不下载 raw 报告')
    L.append('- fixture 数据：仅用于框架测试，未用于投研判断')
    L.append('')
    L.append('## 3. 当前结论')
    L.append('')
    if b.get('real_data_available'):
        L.append('真实结构化财务数据接入成功。Phase 56 建立了从真实数据源到投研简报的完整链路。')
    else:
        L.append('当前未取得真实结构化财务数据，无法形成真实财务判断。')
    L.append('不生成投资建议，不进入 pending/order/trade。')
    L.append('')
    L.append('> 本简报不构成投资建议。')
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
