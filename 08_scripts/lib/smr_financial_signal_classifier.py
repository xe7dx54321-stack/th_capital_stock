#!/usr/bin/env python3
from smr_quarterly_financial_signal_calculator import calculate_quarterly_signals

def classify_financial_signals(ticker='300308.SZ'):
    signals = calculate_quarterly_signals(ticker)
    rows = signals['quarterly_financial_signals']['rows']
    missing = signals['quarterly_financial_signals']['missing_reasons']

    positive = [s for s in rows if s['signal_direction'] == 'positive']
    negative = [s for s in rows if s['signal_direction'] == 'negative']
    neutral = [s for s in rows if s['signal_direction'] == 'neutral']
    slightly_neg = [s for s in rows if s['signal_direction'] == 'slightly_negative']

    obs = []
    # Build observed-first implications
    for s in rows[:6]:
        sig_name = s['signal']
        direction = s['signal_direction']
        if sig_name == 'revenue_yoy' and direction == 'positive':
            obs.append({'observation': '收入同比为正', 'implication': '支持高端产品或出货增长可能已经进入收入端', 'confidence': 'fixture_only'})
        elif sig_name == 'revenue_qoq' and direction == 'positive':
            obs.append({'observation': '收入环比为正', 'implication': '出货节奏保持正向', 'confidence': 'fixture_only'})
        elif sig_name == 'inventory_yoy' and direction == 'slightly_negative':
            obs.append({'observation': '存货同比增长偏高', 'implication': '可能反映备货增加，但也可能是渠道库存积压', 'confidence': 'fixture_only'})
        elif sig_name == 'contract_liabilities_yoy' and direction == 'positive':
            obs.append({'observation': '合同负债同比增长', 'implication': '可能反映订单预收款增加', 'confidence': 'fixture_only'})

    total_pos = len(positive); total_neg = len(negative) + len(slightly_neg)
    if total_pos > total_neg: overall = 'mostly_positive_or_fixture_only'
    elif total_neg > total_pos: overall = 'mixed_or_fixture_only'
    else: overall = 'mixed_or_fixture_only'

    return {'ticker': ticker, 'financial_signal_classification': {
        'overall_status': overall,
        'positive_signals': [s['signal']+'_'+s['period'] for s in positive],
        'negative_signals': [s['signal']+'_'+s['period'] for s in negative + slightly_neg],
        'insufficient_data': list(missing.keys()),
        'observed_implications': obs,
        'fixture_note': 'Classification based on fixture data only. Does not represent real financial analysis.'
    }}
