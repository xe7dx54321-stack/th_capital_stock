#!/usr/bin/env python3
from __future__ import annotations

# Fixture data for 300308.SZ - clearly marked as fixture_only
FIXTURE_RECORDS = [
    {'period': '2024Q4', 'period_type': 'single_quarter', 'metric': 'revenue', 'value': 4800000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q1', 'period_type': 'single_quarter', 'metric': 'revenue', 'value': 5200000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q2', 'period_type': 'single_quarter', 'metric': 'revenue', 'value': 6500000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2024Q4', 'period_type': 'single_quarter', 'metric': 'net_profit', 'value': 950000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q1', 'period_type': 'single_quarter', 'metric': 'net_profit', 'value': 1050000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q2', 'period_type': 'single_quarter', 'metric': 'net_profit', 'value': 1300000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2024Q4', 'period_type': 'single_quarter', 'metric': 'inventory', 'value': 3200000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q1', 'period_type': 'single_quarter', 'metric': 'inventory', 'value': 3800000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q2', 'period_type': 'single_quarter', 'metric': 'inventory', 'value': 4100000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2024Q4', 'period_type': 'single_quarter', 'metric': 'contract_liabilities', 'value': 1800000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q1', 'period_type': 'single_quarter', 'metric': 'contract_liabilities', 'value': 2200000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'},
    {'period': '2025Q2', 'period_type': 'single_quarter', 'metric': 'contract_liabilities', 'value': 2500000000, 'unit': 'CNY', 'source_type': 'manual_financial_fixture'}
]

def load_financial_statements(ticker='300308.SZ', mode='dry-run'):
    is_dry = mode == 'dry-run'
    records = FIXTURE_RECORDS
    periods = sorted(set(r['period'] for r in records))
    metrics = sorted(set(r['metric'] for r in records))
    return {'ticker': ticker, 'financial_statement_loader': {
        'mode': mode,
        'records_loaded': len(records),
        'periods_loaded': periods,
        'metrics_loaded': metrics,
        'fixture_used': True,
        'raw_content_saved': False,
        'records_written': 0 if is_dry else len(records),
        'records': records,
        'note': 'All data is manual_financial_fixture. Does NOT represent real financial data. Fixture data is for framework testing only.'
    }}
