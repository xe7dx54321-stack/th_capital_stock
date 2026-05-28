#!/usr/bin/env python3
from smr_financial_metric_normalizer import normalize_financial_metrics

def calculate_quarterly_signals(ticker='300308.SZ'):
    norm = normalize_financial_metrics(ticker)
    rows = norm['financial_metric_normalization']['rows']
    missing = norm['financial_metric_normalization']['missing_metrics']

    by_period_metric = {}
    for r in rows:
        k = (r['period'], r['metric'])
        by_period_metric[k] = r['value']

    periods = sorted(set(r['period'] for r in rows))
    signals = []
    missing_signals = {}

    # Revenue YoY
    for p in periods:
        year = int(p[:4])
        q = p[4:]
        prev_year_period = str(year - 1) + q
        curr = by_period_metric.get((p, 'revenue'))
        prev = by_period_metric.get((prev_year_period, 'revenue'))
        if curr is not None and prev is not None and prev != 0:
            yoy = (curr - prev) / prev
            signals.append({'signal': 'revenue_yoy', 'period': p, 'value': round(yoy, 4), 'signal_direction': 'positive' if yoy > 0.05 else ('negative' if yoy < -0.05 else 'neutral'), 'confidence': 'fixture_only'})
        else:
            missing_signals['revenue_yoy_'+p] = 'insufficient_comparable_period'

    # Net Profit YoY
    for p in periods:
        year = int(p[:4])
        q = p[4:]
        prev_year_period = str(year - 1) + q
        curr = by_period_metric.get((p, 'net_profit'))
        prev = by_period_metric.get((prev_year_period, 'net_profit'))
        if curr is not None and prev is not None and prev != 0:
            yoy = (curr - prev) / prev
            signals.append({'signal': 'net_profit_yoy', 'period': p, 'value': round(yoy, 4), 'signal_direction': 'positive' if yoy > 0.05 else ('negative' if yoy < -0.05 else 'neutral'), 'confidence': 'fixture_only'})

    # Revenue QoQ
    qoq_map = {'Q1': 'Q4', 'Q2': 'Q1', 'Q3': 'Q2', 'Q4': 'Q3'}
    for p in periods:
        year = int(p[:4]); q = p[4:]
        prev_q = qoq_map.get(q)
        if prev_q:
            prev_year = year if q != 'Q1' else year - 1
            prev_period = str(prev_year) + prev_q
            curr = by_period_metric.get((p, 'revenue'))
            prev = by_period_metric.get((prev_period, 'revenue'))
            if curr is not None and prev is not None and prev != 0:
                qoq = (curr - prev) / prev
                signals.append({'signal': 'revenue_qoq', 'period': p, 'value': round(qoq, 4), 'signal_direction': 'positive' if qoq > 0.03 else ('negative' if qoq < -0.03 else 'neutral'), 'confidence': 'fixture_only'})

    # Net Profit QoQ
    for p in periods:
        year = int(p[:4]); q = p[4:]
        prev_q = qoq_map.get(q)
        if prev_q:
            prev_year = year if q != 'Q1' else year - 1
            prev_period = str(prev_year) + prev_q
            curr = by_period_metric.get((p, 'net_profit'))
            prev = by_period_metric.get((prev_period, 'net_profit'))
            if curr is not None and prev is not None and prev != 0:
                qoq = (curr - prev) / prev
                signals.append({'signal': 'net_profit_qoq', 'period': p, 'value': round(qoq, 4), 'signal_direction': 'positive' if qoq > 0.03 else ('negative' if qoq < -0.03 else 'neutral'), 'confidence': 'fixture_only'})

    # Inventory YoY and inventory_to_revenue
    for p in periods:
        year = int(p[:4]); q = p[4:]
        prev_yr = str(year - 1) + q
        curr_inv = by_period_metric.get((p, 'inventory'))
        prev_inv = by_period_metric.get((prev_yr, 'inventory'))
        curr_rev = by_period_metric.get((p, 'revenue'))
        if curr_inv is not None and prev_inv is not None and prev_inv != 0:
            yoy = (curr_inv - prev_inv) / prev_inv
            signals.append({'signal': 'inventory_yoy', 'period': p, 'value': round(yoy, 4), 'signal_direction': 'slightly_negative' if yoy > 0.3 else ('neutral' if yoy > 0 else 'positive'), 'confidence': 'fixture_only'})
        if curr_inv is not None and curr_rev is not None and curr_rev != 0:
            ratio = curr_inv / curr_rev
            signals.append({'signal': 'inventory_to_revenue', 'period': p, 'value': round(ratio, 4), 'signal_direction': 'neutral', 'confidence': 'fixture_only'})

    # Contract liabilities YoY
    for p in periods:
        year = int(p[:4]); q = p[4:]
        prev_yr = str(year - 1) + q
        curr_cl = by_period_metric.get((p, 'contract_liabilities'))
        prev_cl = by_period_metric.get((prev_yr, 'contract_liabilities'))
        if curr_cl is not None and prev_cl is not None and prev_cl != 0:
            yoy = (curr_cl - prev_cl) / prev_cl
            direction = 'positive' if yoy > 0.1 else ('neutral' if yoy > 0 else 'negative')
            signals.append({'signal': 'contract_liabilities_yoy', 'period': p, 'value': round(yoy, 4), 'signal_direction': direction, 'confidence': 'fixture_only'})

    for m in missing:
        missing_signals[m] = 'metric_not_available'

    return {'ticker': ticker, 'quarterly_financial_signals': {
        'periods_checked': len(periods),
        'signals_calculated': len(signals),
        'signals_missing': len(missing_signals),
        'rows': signals,
        'missing_reasons': missing_signals,
        'fixture_note': 'All signals calculated from fixture data. Does not represent real financial analysis.'
    }}
