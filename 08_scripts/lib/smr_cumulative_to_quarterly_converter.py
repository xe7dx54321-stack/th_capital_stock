#!/usr/bin/env python3
import sys, json
from collections import defaultdict

# Metrics that are cumulative (income statement / cash flow) and should be differenced
CUMULATIVE_METRICS = {
    'revenue', 'net_profit', 'operating_profit', 'cost_of_revenue',
    'operating_cash_flow', 'capex',
}

# Balance sheet metrics are period-end snapshots - no differencing
BALANCE_SHEET_METRICS = {
    'inventory', 'accounts_receivable', 'contract_liabilities',
    'total_assets', 'total_liabilities',
}


def convert_cumulative_to_single_quarter(records):
    by_metric_period = defaultdict(dict)
    for r in records:
        metric = r['metric']
        period = r['period']
        period_type = r.get('period_type', '')
        value = r['value']
        # Only process cumulative records
        if period_type != 'cumulative':
            continue
        by_metric_period[metric][period] = value

    single_quarter_records = []
    balance_skipped = []
    warnings = []

    for metric, period_values in sorted(by_metric_period.items()):
        if metric in BALANCE_SHEET_METRICS:
            balance_skipped.append(metric)
            continue

        periods = sorted(period_values.keys())
        for i, period in enumerate(periods):
            year = int(period[:4])
            quarter = period[4:]

            if quarter == 'Q1':
                # Q1 cumulative = Q1 standalone
                sq_value = period_values[period]
                method = 'q1_identity'
            elif quarter == 'Q2':
                q1_period = str(year) + 'Q1'
                if q1_period in period_values:
                    sq_value = period_values[period] - period_values[q1_period]
                    method = 'q2_minus_q1'
                else:
                    sq_value = None
                    warnings.append(f'{metric} {period}: missing Q1 cumulative for Q2 single-quarter derivation')
            elif quarter == 'Q3':
                q2_period = str(year) + 'Q2'
                if q2_period in period_values:
                    sq_value = period_values[period] - period_values[q2_period]
                    method = 'q3_minus_q2'
                else:
                    sq_value = None
                    warnings.append(f'{metric} {period}: missing Q2 cumulative for Q3 single-quarter derivation')
            elif quarter == 'Q4':
                q3_period = str(year) + 'Q3'
                if q3_period in period_values:
                    sq_value = period_values[period] - period_values[q3_period]
                    method = 'q4_minus_q3'
                else:
                    sq_value = None
                    warnings.append(f'{metric} {period}: missing Q3 cumulative for Q4 single-quarter derivation')
            else:
                sq_value = None
                method = 'unknown_quarter'

            if sq_value is not None:
                single_quarter_records.append({
                    'period': period,
                    'period_type': 'single_quarter',
                    'derivation': method,
                    'derived_from': 'cumulative',
                    'metric': metric,
                    'value': sq_value,
                    'unit': 'CNY',
                    'source_type': 'real_structured_derived_single_quarter',
                    'confidence': 'real_structured_derived_single_quarter',
                })

    return {
        'cumulative_records_checked': len(records),
        'single_quarter_records_created': len(single_quarter_records),
        'metrics_converted': sorted(set(r['metric'] for r in single_quarter_records)),
        'balance_sheet_metrics_skipped': balance_skipped,
        'conversion_warnings': warnings,
        'single_quarter_records': single_quarter_records,
    }
