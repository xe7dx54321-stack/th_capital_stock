#!/usr/bin/env python3
from smr_financial_statement_loader import load_financial_statements

METRIC_NAME_MAP = {'revenue': 'revenue','net_profit': 'net_profit','inventory': 'inventory','contract_liabilities': 'contract_liabilities'}

def normalize_financial_metrics(ticker='300308.SZ'):
    loader_result = load_financial_statements(ticker, 'execute')
    records = loader_result['financial_statement_loader']['records']
    normalized = []
    for r in records:
        norm_name = METRIC_NAME_MAP.get(r['metric'], r['metric'])
        normalized.append({
            'metric': norm_name,
            'period': r['period'],
            'period_type': r.get('period_type','single_quarter'),
            'value': r['value'],
            'unit': r.get('unit','CNY'),
            'source_type': r.get('source_type','manual_financial_fixture'),
            'confidence': 'fixture_only'
        })
    all_metrics = set(r['metric'] for r in records)
    schema_metrics = ['revenue','gross_profit','net_profit','inventory','contract_liabilities','accounts_receivable','operating_cash_flow','capex']
    missing = [m for m in schema_metrics if m not in all_metrics]
    return {'ticker': ticker, 'financial_metric_normalization': {
        'raw_metrics_checked': len(records),
        'normalized_metrics': len(normalized),
        'missing_metrics': missing,
        'periods_detected': sorted(set(r['period'] for r in normalized)),
        'rows': normalized,
        'fixture_note': 'All values are fixture data. Does not represent real financial data.'
    }}
