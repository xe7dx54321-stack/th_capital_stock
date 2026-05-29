#!/usr/bin/env python3
from smr_structured_financial_data_adapter import fetch_structured_financial_data
from smr_cumulative_to_quarterly_converter import convert_cumulative_to_single_quarter
from collections import defaultdict


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return round((a - b) / abs(b), 4)


def _direction(val, pos_thresh=0.05, neg_thresh=-0.05):
    if val is None:
        return 'unknown'
    if val > pos_thresh:
        return 'positive'
    if val < neg_thresh:
        return 'negative'
    return 'neutral'


def calculate_refined_quarterly_signals(ticker='300308.SZ'):
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    records = fetch_result['structured_financial_data_fetch']['records']
    real_available = fetch_result['structured_financial_data_fetch'].get('real_data_available', False)
    fixture_used = fetch_result['structured_financial_data_fetch'].get('fixture_used', False)

    conversion = convert_cumulative_to_single_quarter(records)
    sq_records = conversion['single_quarter_records']

    # Build lookup: metric -> period -> value (single quarter)
    sq_by = defaultdict(dict)
    for r in sq_records:
        sq_by[r['metric']][r['period']] = r['value']

    # Build lookup for cumulative balance sheet items
    bs_by = defaultdict(dict)
    for r in records:
        if r.get('period_type') != 'cumulative':
            continue
        bs_by[r['metric']][r['period']] = r['value']

    all_periods = sorted(set(r['period'] for r in sq_records))
    signals = []
    missing_reasons = {}

    def _yoy(metric, label, periods, source_dict):
        for p in periods:
            year = int(p[:4]); q = p[4:]
            prev = str(year - 1) + q
            curr = source_dict.get(metric, {}).get(p)
            prev_v = source_dict.get(metric, {}).get(prev)
            if curr is not None and prev_v is not None and prev_v != 0:
                v = _safe_div(curr, prev_v)
                if v is not None:
                    conf = 'real_structured_derived_single_quarter' if metric in {'revenue','net_profit','operating_profit','cost_of_revenue','operating_cash_flow','capex'} else 'real_structured'
                    signals.append({'signal': label, 'period': p, 'value': v, 'direction': _direction(v), 'confidence': conf})
            elif curr is None or prev_v is None:
                missing_reasons.setdefault(label + '_' + p, 'insufficient_data_for_yoy')

    def _qoq(metric, label, periods, source_dict):
        qoq_map = {'Q1': 'Q4', 'Q2': 'Q1', 'Q3': 'Q2', 'Q4': 'Q3'}
        for p in periods:
            year = int(p[:4]); q = p[4:]
            prev_q = qoq_map.get(q)
            if not prev_q:
                continue
            prev_yr = year if q != 'Q1' else year - 1
            prev_p = str(prev_yr) + prev_q
            curr = source_dict.get(metric, {}).get(p)
            prev_v = source_dict.get(metric, {}).get(prev_p)
            if curr is not None and prev_v is not None and prev_v != 0:
                v = _safe_div(curr, prev_v)
                if v is not None:
                    conf = 'real_structured_derived_single_quarter' if metric in {'revenue','net_profit','operating_profit','cost_of_revenue','operating_cash_flow','capex'} else 'real_structured'
                    signals.append({'signal': label, 'period': p, 'value': v, 'direction': _direction(v, 0.03, -0.03), 'confidence': conf})
            elif curr is None or prev_v is None:
                missing_reasons.setdefault(label + '_' + p, 'insufficient_data_for_qoq')

    # Single quarter revenue YoY / QoQ
    _yoy('revenue', 'single_quarter_revenue_yoy', all_periods, sq_by)
    _qoq('revenue', 'single_quarter_revenue_qoq', all_periods, sq_by)

    # Single quarter net profit YoY / QoQ
    _yoy('net_profit', 'single_quarter_net_profit_yoy', all_periods, sq_by)
    _qoq('net_profit', 'single_quarter_net_profit_qoq', all_periods, sq_by)

    # Gross margin (using cost_of_revenue to derive gross profit)
    # gross_profit = revenue - cost_of_revenue (single quarter)
    for p in all_periods:
        rev = sq_by.get('revenue', {}).get(p)
        cost = sq_by.get('cost_of_revenue', {}).get(p)
        if rev is not None and cost is not None and rev != 0:
            gm = round((rev - cost) / rev, 4)
            signals.append({'signal': 'gross_margin', 'period': p, 'value': gm, 'direction': 'positive' if gm > 0.3 else ('negative' if gm < 0.15 else 'neutral'), 'confidence': 'real_structured_derived_single_quarter'})
        else:
            missing_reasons.setdefault('gross_margin_' + p, 'missing_revenue_or_cost_of_revenue')

    # Gross margin YoY/QoQ delta (comparing gm level)
    gm_by_p = {}
    for s in signals:
        if s['signal'] == 'gross_margin':
            gm_by_p[s['period']] = s['value']
    for p in all_periods:
        year = int(p[:4]); q = p[4:]
        prev = str(year - 1) + q
        if p in gm_by_p and prev in gm_by_p:
            delta = round(gm_by_p[p] - gm_by_p[prev], 4)
            signals.append({'signal': 'gross_margin_yoy_delta', 'period': p, 'value': delta, 'direction': 'positive' if delta > 0.01 else ('negative' if delta < -0.01 else 'neutral'), 'confidence': 'real_structured_derived_single_quarter'})
        qoq_map = {'Q1': 'Q4', 'Q2': 'Q1', 'Q3': 'Q2', 'Q4': 'Q3'}
        prev_q = qoq_map.get(q)
        if prev_q:
            prev_yr = year if q != 'Q1' else year - 1
            prev_p = str(prev_yr) + prev_q
            if p in gm_by_p and prev_p in gm_by_p:
                delta = round(gm_by_p[p] - gm_by_p[prev_p], 4)
                signals.append({'signal': 'gross_margin_qoq_delta', 'period': p, 'value': delta, 'direction': 'positive' if delta > 0.01 else ('negative' if delta < -0.01 else 'neutral'), 'confidence': 'real_structured_derived_single_quarter'})

    # Net margin
    for p in all_periods:
        rev = sq_by.get('revenue', {}).get(p)
        np_ = sq_by.get('net_profit', {}).get(p)
        if rev is not None and np_ is not None and rev != 0:
            nm = round(np_ / rev, 4)
            signals.append({'signal': 'net_margin', 'period': p, 'value': nm, 'direction': 'positive' if nm > 0.1 else ('negative' if nm < 0.03 else 'neutral'), 'confidence': 'real_structured_derived_single_quarter'})

    # Operating profit margin
    for p in all_periods:
        rev = sq_by.get('revenue', {}).get(p)
        op = sq_by.get('operating_profit', {}).get(p)
        if rev is not None and op is not None and rev != 0:
            opm = round(op / rev, 4)
            signals.append({'signal': 'operating_profit_margin', 'period': p, 'value': opm, 'direction': 'positive' if opm > 0.1 else 'neutral', 'confidence': 'real_structured_derived_single_quarter'})

    # Inventory to revenue
    for p in all_periods:
        inv = bs_by.get('inventory', {}).get(p)
        rev = sq_by.get('revenue', {}).get(p)
        if inv is not None and rev is not None and rev != 0:
            ratio = round(inv / rev, 4)
            signals.append({'signal': 'inventory_to_revenue', 'period': p, 'value': ratio, 'direction': 'positive' if ratio < 0.3 else ('negative' if ratio > 0.5 else 'neutral'), 'confidence': 'real_structured'})

    # Accounts receivable to revenue
    for p in all_periods:
        ar = bs_by.get('accounts_receivable', {}).get(p)
        rev = sq_by.get('revenue', {}).get(p)
        if ar is not None and rev is not None and rev != 0:
            ratio = round(ar / rev, 4)
            signals.append({'signal': 'accounts_receivable_to_revenue', 'period': p, 'value': ratio, 'direction': 'negative' if ratio > 0.5 else 'neutral', 'confidence': 'real_structured'})

    # Contract liabilities YoY
    _yoy('contract_liabilities', 'contract_liabilities_yoy', all_periods, bs_by)

    # Operating cash flow to net profit
    for p in all_periods:
        ocf = sq_by.get('operating_cash_flow', {}).get(p)
        np_ = sq_by.get('net_profit', {}).get(p)
        if ocf is not None and np_ is not None and np_ != 0:
            ratio = round(ocf / np_, 4)
            signals.append({'signal': 'operating_cash_flow_to_net_profit', 'period': p, 'value': ratio, 'direction': 'positive' if ratio > 0.8 else ('negative' if ratio < 0.3 else 'neutral'), 'confidence': 'real_structured_derived_single_quarter'})

    # Capex YoY / Capex to revenue
    _yoy('capex', 'capex_yoy', all_periods, sq_by)
    for p in all_periods:
        capex_val = sq_by.get('capex', {}).get(p)
        rev = sq_by.get('revenue', {}).get(p)
        if capex_val is not None and rev is not None and rev != 0:
            ratio = round(capex_val / rev, 4)
            signals.append({'signal': 'capex_to_revenue', 'period': p, 'value': ratio, 'direction': 'neutral', 'confidence': 'real_structured_derived_single_quarter'})

    # Latest period summary
    latest = max(all_periods) if all_periods else 'unknown'
    latest_signals = [s for s in signals if s['period'] == latest]

    return {
        'ticker': ticker,
        'refined_quarterly_financial_signals': {
            'real_data_used': real_available,
            'fixture_used': fixture_used,
            'single_quarter_used': True,
            'periods_checked': len(all_periods),
            'latest_period': latest,
            'signals_calculated': len(signals),
            'signals_missing': len(missing_reasons),
            'latest_signals': latest_signals,
            'all_signals': signals,
            'missing_reasons': missing_reasons,
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }
