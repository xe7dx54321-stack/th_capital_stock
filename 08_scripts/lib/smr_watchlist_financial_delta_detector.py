#!/usr/bin/env python3
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables


def detect_watchlist_financial_delta(ticker='300308.SZ', previous_snapshot=None):
    current = map_signals_to_industry_variables(ticker)
    current_rows = current['financial_signal_to_industry_variable_map']['rows']

    # First run: use current as baseline
    if previous_snapshot is None:
        delta_rows = []
        for r in current_rows:
            status = r['variable_status']
            if status == 'supported_by_financial_signal':
                delta = 'strengthened'
            elif status == 'partially_supported':
                delta = 'newly_observable'
            elif status == 'weakened_by_financial_signal':
                delta = 'weakened'
            else:
                delta = 'unjudgeable'
            delta_rows.append({
                'industry_variable': r['industry_variable'],
                'delta': delta,
                'current_status': status,
                'observation': r.get('interpretation', ''),
                'cannot_conclude': r.get('cannot_conclude', []),
            })
        note = 'first_run_baseline_established'
    else:
        # Compare against previous
        prev_map = {r['industry_variable']: r['variable_status'] for r in previous_snapshot.get('rows', [])}
        delta_rows = []
        for r in current_rows:
            prev_status = prev_map.get(r['industry_variable'], 'unknown')
            curr_status = r['variable_status']
            if curr_status == prev_status:
                delta = 'unchanged'
            elif curr_status == 'supported_by_financial_signal' and prev_status in ('partially_supported', 'not_observable_from_financials'):
                delta = 'strengthened'
            elif curr_status == 'weakened_by_financial_signal' and prev_status != 'weakened_by_financial_signal':
                delta = 'weakened'
            elif curr_status == 'not_observable_from_financials':
                delta = 'became_unobservable'
            else:
                delta = 'unchanged'
            delta_rows.append({
                'industry_variable': r['industry_variable'],
                'delta': delta,
                'current_status': curr_status,
                'previous_status': prev_status,
                'observation': r.get('interpretation', ''),
                'cannot_conclude': r.get('cannot_conclude', []),
            })
        note = 'compared_against_previous_snapshot'

    strengthened = sum(1 for r in delta_rows if r['delta'] == 'strengthened')
    weakened = sum(1 for r in delta_rows if r['delta'] == 'weakened')
    unchanged = sum(1 for r in delta_rows if r['delta'] == 'unchanged')
    unjudgeable = sum(1 for r in delta_rows if r['delta'] == 'unjudgeable')

    return {
        'ticker': ticker,
        'watchlist_financial_delta': {
            'note': note,
            'variables_checked': len(delta_rows),
            'variables_strengthened': strengthened,
            'variables_weakened': weakened,
            'variables_unchanged': unchanged,
            'variables_unjudgeable': unjudgeable,
            'rows': delta_rows,
            'delta_summary': (
                'finance_variables_mostly_strengthened_but_key_customer_variables_unconfirmed'
                if strengthened > 0 and unjudgeable > 0 else
                'finance_variables_mixed'
            ),
        }
    }
