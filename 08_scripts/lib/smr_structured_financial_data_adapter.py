#!/usr/bin/env python3
from __future__ import annotations
import math

# Column mapping for akshare/sina financial statements
INCOME_MAP = {
    '营业总收入': 'revenue',
    '营业利润': 'operating_profit',
    '净利润': 'net_profit',
    '营业成本': 'cost_of_revenue',
}
BALANCE_MAP = {
    '存货': 'inventory',
    '合同负债': 'contract_liabilities',
    '应收账款': 'accounts_receivable',
    '资产总计': 'total_assets',
    '负债合计': 'total_liabilities',
}
CASHFLOW_MAP = {
    '经营活动产生的现金流量净额': 'operating_cash_flow',
    '购建固定资产、无形资产和其他长期资产支付的现金': 'capex',
}
def _to_q(period_str):
    s = str(period_str).strip()
    if len(s) < 8: return ''
    yr = s[:4]; md = s[4:]
    qmap = {'0331': 'Q1', '0630': 'Q2', '0930': 'Q3', '1231': 'Q4'}
    q = qmap.get(md, '')
    return yr + q if q else ''

def _safe_float(val):
    if val is None: return None
    try:
        fv = float(val)
        if math.isnan(fv) or math.isinf(fv): return None
        return fv
    except (ValueError, TypeError): return None

def _find_capex_col(df):
    for col in df.columns:
        s = str(col)
        if '固定资产' in s and '支付' in s and '处置' not in s:
            return s
    return None

def _extract(df, col_map):
    records = []
    period_col = df.columns[0]
    has_capex = any('capex' in str(v) for v in col_map.values())
    capex_col = _find_capex_col(df) if has_capex else None
    for _, row in df.iterrows():
        period = _to_q(row[period_col])
        if not period: continue
        for cn_name, our_name in col_map.items():
            actual_col = cn_name
            if cn_name not in df.columns:
                if 'capex' in our_name and capex_col:
                    actual_col = capex_col
                else:
                    continue
            fv = _safe_float(row[actual_col])
            if fv is not None and fv != 0:
                records.append({'period': period, 'period_type': 'cumulative', 'metric': our_name, 'value': fv, 'unit': 'CNY', 'source_type': 'akshare_sina_financial', 'confidence': 'real_structured'})
    return records
def fetch_structured_financial_data(ticker='300308.SZ', mode='dry-run'):
    is_dry = mode == 'dry-run'
    skip_net = mode == 'skip-network'
    code = 'sz' + ticker[:6] if '.SZ' in ticker else 'sh' + ticker[:6]
    
    if skip_net or is_dry:
        return {'ticker': ticker, 'structured_financial_data_fetch': {
            'mode': mode, 'real_data_available': False,
            'source_id': 'akshare_sina_financial',
            'records_loaded': 0, 'periods_loaded': [], 'metrics_loaded': [],
            'confidence': 'unavailable', 'fixture_used': False,
            'raw_content_saved': False,
            'reason': 'dry_run_no_fetch' if is_dry else 'skip_network_requested',
            'records_written': 0, 'records': []}}
    
    records = []
    errors = []
    try:
        import akshare as ak
        
        for symbol, col_map in [('利润表', INCOME_MAP), ('资产负债表', BALANCE_MAP), ('现金流量表', CASHFLOW_MAP)]:
            try:
                df = ak.stock_financial_report_sina(stock=code, symbol=symbol)
                recs = _extract(df, col_map)
                records.extend(recs)
            except Exception as e:
                errors.append(f'{symbol}: {e}')
        
        periods = sorted(set(r['period'] for r in records))
        metrics = sorted(set(r['metric'] for r in records))
        return {'ticker': ticker, 'structured_financial_data_fetch': {
            'mode': mode, 'real_data_available': len(records) > 0,
            'source_id': 'akshare_sina_financial',
            'records_loaded': len(records), 'periods_loaded': periods,
            'metrics_loaded': metrics,
            'confidence': 'real_structured', 'fixture_used': False,
            'raw_content_saved': False, 'errors': errors,
            'records_written': len(records), 'records': records,
            'note': 'Real structured financial data via akshare/sina. Cumulative period type. Capex uses fuzzy column matching.'}}
    except ImportError:
        return {'ticker': ticker, 'structured_financial_data_fetch': {
            'mode': mode, 'real_data_available': False, 'source_id': None,
            'records_loaded': 0, 'confidence': 'unavailable',
            'reason': 'akshare_not_installed', 'records_written': 0}}
    except Exception as e:
        return {'ticker': ticker, 'structured_financial_data_fetch': {
            'mode': mode, 'real_data_available': False,
            'source_id': 'akshare_sina_financial',
            'records_loaded': 0, 'confidence': 'unavailable',
            'reason': str(e) + '; '.join(errors), 'records_written': 0}}
