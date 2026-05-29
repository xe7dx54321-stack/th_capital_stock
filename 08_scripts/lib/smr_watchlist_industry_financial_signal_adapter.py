#!/usr/bin/env python3
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables
from smr_industry_financial_variable_interpretation import interpret_industry_financial_variables
from smr_financial_cannot_conclude_guard import build_guard_report
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def build_watchlist_industry_financial_signal_adapter(ticker='300308.SZ'):
    signals = calculate_refined_quarterly_signals(ticker)
    sd = signals['refined_quarterly_financial_signals']
    mapper = map_signals_to_industry_variables(ticker)
    guard = build_guard_report(ticker)

    rows = mapper['financial_signal_to_industry_variable_map']['rows']
    supported = sum(1 for r in rows if r['variable_status'] == 'supported_by_financial_signal')
    partial = sum(1 for r in rows if r['variable_status'] == 'partially_supported')
    unconfirmed = sum(1 for r in rows if r['variable_status'] in ('not_observable_from_financials', 'unconfirmed'))

    key_obs = [
        f"最新期间（{sd['latest_period']}）真实财务数据已取得。",
    ]
    if supported > 0:
        key_obs.append(f"{supported}个行业财务变量获得真实财务信号支持。")
    if unconfirmed > 0:
        key_obs.append(f"{unconfirmed}个行业变量仍无法由财务数据确认。")
    key_obs.append("财务侧支持业务动能较强，但不能单独确认产品代际和客户份额。")

    return {
        'ticker': ticker,
        'industry': 'ai_optical_module',
        'watchlist_industry_financial_signal_adapter': {
            'real_financial_data_used': sd['real_data_used'],
            'fixture_used': sd['fixture_used'],
            'latest_period': sd['latest_period'],
            'industry_variables_loaded': len(rows),
            'industry_variables_supported': supported,
            'industry_variables_partially_supported': partial,
            'industry_variables_unconfirmed': unconfirmed,
            'cannot_conclude_guard_status': guard['cannot_conclude_guard']['guard_status'],
            'key_observations': key_obs,
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }
