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


EXPECTED_METRICS = [
    'revenue', 'net_profit', 'gross_margin', 'inventory',
    'accounts_receivable', 'contract_liabilities',
    'operating_cash_flow', 'capex'
]


def build(conn, ticker):
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    records = fetch_result['structured_financial_data_fetch']['records']
    conversion = convert_cumulative_to_single_quarter(records)

    all_metrics = set(r['metric'] for r in records)
    periods = sorted(set(r['period'] for r in records))
    latest_period = periods[-1] if periods else 'unknown'

    sq_records = conversion['single_quarter_records']
    sq_periods = sorted(set(r['period'] for r in sq_records))

    covered = sorted(all_metrics)
    missing = [m for m in EXPECTED_METRICS if m not in all_metrics]

    return {
        'ticker': ticker,
        'quarterly_metric_coverage': {
            'periods_checked': len(periods),
            'latest_period': latest_period,
            'metrics_covered': covered,
            'metrics_missing': missing,
            'single_quarter_available': len(sq_periods) > 0,
            'cumulative_available': len(periods) > 0,
            'balance_sheet_period_end_available': all(
                m in all_metrics for m in ['inventory', 'accounts_receivable', 'contract_liabilities']
            ),
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['quarterly_metric_coverage']
        print(f"# {args.ticker} Quarterly Metric Coverage")
        print(f"\n- Periods checked: {d['periods_checked']}")
        print(f"- Latest period: {d['latest_period']}")
        print(f"- Metrics covered: {', '.join(d['metrics_covered'])}")
        print(f"- Metrics missing: {', '.join(d['metrics_missing']) if d['metrics_missing'] else 'none'}")
        print(f"- Single quarter available: {d['single_quarter_available']}")
        print(f"- Cumulative available: {d['cumulative_available']}")
        print(f"- Balance sheet period-end available: {d['balance_sheet_period_end_available']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
