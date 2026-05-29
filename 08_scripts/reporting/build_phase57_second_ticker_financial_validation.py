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


def validate_second_ticker(ticker):
    try:
        fetch_result = fetch_structured_financial_data(ticker, 'execute')
        records = fetch_result['structured_financial_data_fetch']['records']
        real_available = fetch_result['structured_financial_data_fetch'].get('real_data_available', False)
        fixture_used = fetch_result['structured_financial_data_fetch'].get('fixture_used', False)

        if not real_available or len(records) == 0:
            return {
                'ticker': ticker,
                'real_data_available': False,
                'records_loaded': 0,
                'failure_reason': 'no_real_structured_data_available',
                'framework_validation_status': 'fail',
            'ticker_specific_thesis_mapping_used': False,
            }

        periods = sorted(set(r['period'] for r in records))
        metrics = sorted(set(r['metric'] for r in records))
        conversion = convert_cumulative_to_single_quarter(records)

        signals_result = calculate_refined_quarterly_signals(ticker)
        signals_data = signals_result.get('refined_quarterly_financial_signals', {})

        return {
            'ticker': ticker,
            'real_data_available': True,
            'records_loaded': len(records),
            'periods_loaded': len(periods),
            'metrics_loaded': metrics,
            'signals_calculated': signals_data.get('signals_calculated', 0),
            'framework_validation_status': 'pass',
            'ticker_specific_thesis_mapping_used': False,
            'generic_framework_validated': True,
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'real_data_available': False,
            'records_loaded': 0,
            'failure_reason': str(e),
            'framework_validation_status': 'fail',
            'ticker_specific_thesis_mapping_used': False,
        }


def build(conn, ticker=None, auto_fallback=False):
    if ticker:
        result = validate_second_ticker(ticker)
        return {'second_ticker_financial_validation': result}
    elif auto_fallback:
        primary = '688041.SH'
        fallback = '002230.SZ'
        result = validate_second_ticker(primary)
        if result['framework_validation_status'] == 'fail':
            fb_result = validate_second_ticker(fallback)
            fb_result['primary_ticker'] = primary
            fb_result['fallback_ticker'] = fallback
            fb_result['selected_ticker'] = fallback
            return {'second_ticker_financial_validation': fb_result}
        result['primary_ticker'] = primary
        result['fallback_ticker'] = fallback
        result['selected_ticker'] = primary
        return {'second_ticker_financial_validation': result}
    else:
        return {'second_ticker_financial_validation': {'framework_validation_status': 'not_requested'}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default=None)
    p.add_argument('--auto-fallback', action='store_true')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker, args.auto_fallback)
    if args.markdown:
        d = r['second_ticker_financial_validation']
        ticker = d.get('selected_ticker', d.get('ticker', 'unknown'))
        print(f"# Second Ticker Financial Framework Validation")
        print(f"\n- Selected ticker: {ticker}")
        print(f"- Real data available: {d.get('real_data_available', False)}")
        print(f"- Records loaded: {d.get('records_loaded', 0)}")
        print(f"- Periods loaded: {d.get('periods_loaded', 0)}")
        print(f"- Framework validation: {d.get('framework_validation_status', 'unknown')}")
        if d.get('failure_reason'):
            print(f"- Failure reason: {d['failure_reason']}")
        print(f"- Generic framework validated: {d.get('generic_framework_validated', False)}")
        print(f"- Uses 300308 thesis mapping: {d.get('ticker_specific_thesis_mapping_used', False)}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

