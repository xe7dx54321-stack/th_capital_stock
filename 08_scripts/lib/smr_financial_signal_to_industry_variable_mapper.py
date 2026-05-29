#!/usr/bin/env python3
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals
from smr_ai_optical_financial_variable_schema import get_industry_variables

# Mapping rules: industry variable -> (supporting signal patterns, status logic)
VARIABLE_SIGNAL_RULES = {
    'high_end_product_mix_signal': {
        'positive': ['gross_margin', 'gross_margin_yoy_delta'],
        'neutral': ['gross_margin_qoq_delta'],
    },
    'shipment_revenue_conversion': {
        'positive': ['single_quarter_revenue_yoy', 'single_quarter_revenue_qoq'],
        'watch': ['inventory_to_revenue', 'accounts_receivable_to_revenue'],
    },
    'margin_resilience': {
        'positive': ['gross_margin'],
        'watch': ['gross_margin_yoy_delta', 'gross_margin_qoq_delta'],
    },
    'order_visibility_financial_proxy': {
        'positive': ['contract_liabilities_yoy', 'operating_cash_flow_to_net_profit'],
        'watch': ['inventory_to_revenue', 'accounts_receivable_to_revenue'],
    },
    'customer_demand_financial_proxy': {
        'positive': ['single_quarter_revenue_yoy'],
        'watch': ['accounts_receivable_to_revenue', 'operating_cash_flow_to_net_profit'],
    },
    'capacity_preparation_signal': {
        'positive': ['capex_yoy', 'capex_to_revenue'],
        'watch': ['inventory_to_revenue'],
    },
}


def map_signals_to_industry_variables(ticker='300308.SZ'):
    result = calculate_refined_quarterly_signals(ticker)
    all_signals = result['refined_quarterly_financial_signals']['all_signals']
    latest = result['refined_quarterly_financial_signals']['latest_period']
    variables = get_industry_variables()

    # Index latest signals by signal name
    latest_by_name = {}
    for s in all_signals:
        if s['period'] == latest:
            latest_by_name[s['signal']] = s

    rows = []
    for var_def in variables:
        var_name = var_def['variable']
        rules = VARIABLE_SIGNAL_RULES.get(var_name, {})
        cannot_conclude = var_def.get('cannot_conclude_from_financials_alone', [])

        positive_signals = []
        neutral_signals = []
        negative_signals = []

        for sig_name in rules.get('positive', []):
            s = latest_by_name.get(sig_name)
            if s:
                if s['direction'] == 'positive':
                    positive_signals.append(f"{sig_name}_{s['direction']}")
                elif s['direction'] == 'negative':
                    negative_signals.append(f"{sig_name}_{s['direction']}")
                else:
                    neutral_signals.append(f"{sig_name}_{s['direction']}")

        for sig_name in rules.get('watch', []):
            s = latest_by_name.get(sig_name)
            if s:
                neutral_signals.append(f"{sig_name}_{s.get('direction', 'unknown')}")

        # Determine status
        if len(positive_signals) >= 2:
            status = 'supported_by_financial_signal'
        elif len(positive_signals) == 1:
            status = 'partially_supported'
        elif len(negative_signals) > 0:
            status = 'weakened_by_financial_signal'
        else:
            status = 'not_observable_from_financials'

        # Build interpretation
        interpretation = var_def.get('can_support', [''])[0] if var_def.get('can_support') else ''

        rows.append({
            'industry_variable': var_name,
            'description': var_def.get('description', ''),
            'supporting_financial_signals': positive_signals + neutral_signals,
            'variable_status': status,
            'interpretation': interpretation,
            'cannot_conclude': cannot_conclude,
        })

    return {
        'ticker': ticker,
        'industry': 'ai_optical_module',
        'financial_signal_to_industry_variable_map': {
            'signals_checked': len(all_signals),
            'latest_period': latest,
            'industry_variables_mapped': len(rows),
            'rows': rows,
        }
    }
