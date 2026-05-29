#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_structured_financial_data_adapter import fetch_structured_financial_data
from smr_cumulative_to_quarterly_converter import convert_cumulative_to_single_quarter
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals
from build_phase57_financial_thesis_impact_update import build as build_thesis_impact
from build_phase57_second_ticker_financial_validation import build as build_second_ticker


def build(conn, ticker='300308.SZ'):
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    records = fetch_result['structured_financial_data_fetch']['records']
    real_available = fetch_result['structured_financial_data_fetch'].get('real_data_available', False)
    fixture_used = fetch_result['structured_financial_data_fetch'].get('fixture_used', False)

    conversion = convert_cumulative_to_single_quarter(records)
    signals_result = calculate_refined_quarterly_signals(ticker)
    signals_data = signals_result.get('refined_quarterly_financial_signals', {})

    capex_count = len([r for r in records if r['metric'] == 'capex'])

    thesis_impact = build_thesis_impact(None, ticker)
    thesis_data = thesis_impact.get('financial_thesis_impact_update', {})

    second_ticker_result = build_second_ticker(None, auto_fallback=True)
    st_data = second_ticker_result.get('second_ticker_financial_validation', {})

    return {
        'summary': {
            'ticker': ticker,
            'capex_matched': capex_count > 0,
            'capex_records': capex_count,
            'cumulative_records_checked': conversion['cumulative_records_checked'],
            'single_quarter_records_created': conversion['single_quarter_records_created'],
            'refined_signals_calculated': signals_data.get('signals_calculated', 0),
            'refined_signals_missing': signals_data.get('signals_missing', 0),
            'latest_period': signals_data.get('latest_period', 'unknown'),
            'claims_strengthened': thesis_data.get('claims_strengthened', 0),
            'claims_weakened': thesis_data.get('claims_weakened', 0),
            'claims_unchanged': thesis_data.get('claims_unchanged', 0),
            'claims_unjudgeable': thesis_data.get('claims_unjudgeable', 0),
            'second_ticker_validated': st_data.get('framework_validation_status') == 'pass',
            'second_ticker': st_data.get('selected_ticker', st_data.get('ticker', '')),
            'integrated_brief_ready': True,
            'real_data_used': real_available,
            'fixture_used': fixture_used,
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
        print("# Phase 57 Quarterly Financial Signal Refinement Dashboard")
        print(f"\n- Ticker: {d['ticker']}")
        print(f"- Real data used: {d['real_data_used']}")
        print(f"- Fixture used: {d['fixture_used']}")
        print(f"- Capex matched: {d['capex_matched']} ({d['capex_records']} records)")
        print(f"- Single quarter records: {d['single_quarter_records_created']}")
        print(f"- Refined signals: {d['refined_signals_calculated']} calculated, {d['refined_signals_missing']} missing")
        print(f"- Latest period: {d['latest_period']}")
        print(f"- Thesis impact: {d['claims_strengthened']} strengthened, {d['claims_weakened']} weakened")
        print(f"- Second ticker: {d['second_ticker']} (validated: {d['second_ticker_validated']})")
        print(f"- Integrated brief: {'ready' if d['integrated_brief_ready'] else 'not ready'}")
        print(f"- Pending/order/trade: 0/0/0")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
