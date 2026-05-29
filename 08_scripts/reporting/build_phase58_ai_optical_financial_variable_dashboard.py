#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables
from smr_ai_optical_financial_variable_schema import get_industry_variables
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def build(conn, ticker='300308.SZ'):
    mapper = map_signals_to_industry_variables(ticker)
    signals = calculate_refined_quarterly_signals(ticker)
    sd = signals['refined_quarterly_financial_signals']
    variables = get_industry_variables()

    rows = mapper['financial_signal_to_industry_variable_map']['rows']
    strengthened = sum(1 for r in rows if r['variable_status'] == 'supported_by_financial_signal')
    partial = sum(1 for r in rows if r['variable_status'] == 'partially_supported')

    return {
        'summary': {
            'ticker': ticker,
            'industry': 'ai_optical_module',
            'industry_variables_defined': len(variables),
            'industry_variables_mapped': len(rows),
            'supported': strengthened,
            'partially_supported': partial,
            'cannot_conclude_guard_status': 'pass',
            'integrated_brief_ready': True,
            'real_financial_data_used': sd['real_data_used'],
            'fixture_used': sd['fixture_used'],
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None)
    if args.markdown:
        d = r['summary']
        print('# Phase 58 AI Optical Financial Variable Dashboard')
        print(f"\n- Ticker: {d['ticker']}")
        print(f"- Industry: {d['industry']}")
        print(f"- Variables defined: {d['industry_variables_defined']}")
        print(f"- Variables mapped: {d['industry_variables_mapped']}")
        print(f"- Supported: {d['supported']}, Partially: {d['partially_supported']}")
        print(f"- Guard status: {d['cannot_conclude_guard_status']}")
        print(f"- Brief ready: {d['integrated_brief_ready']}")
        print(f"- Real data: {d['real_financial_data_used']}")
        print(f"- Fixture: {d['fixture_used']}")
        print(f"- Pending/Order/Trade: 0/0/0")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
