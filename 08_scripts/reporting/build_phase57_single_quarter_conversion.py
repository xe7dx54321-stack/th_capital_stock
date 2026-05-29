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


def build(conn, ticker):
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    records = fetch_result['structured_financial_data_fetch']['records']
    conversion = convert_cumulative_to_single_quarter(records)
    return {
        'ticker': ticker,
        'single_quarter_conversion': {
            'cumulative_records_checked': conversion['cumulative_records_checked'],
            'single_quarter_records_created': conversion['single_quarter_records_created'],
            'metrics_converted': conversion['metrics_converted'],
            'balance_sheet_metrics_skipped': conversion['balance_sheet_metrics_skipped'],
            'conversion_warnings': conversion['conversion_warnings'],
            'sample_records': conversion['single_quarter_records'][:6],
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
        d = r['single_quarter_conversion']
        print(f"# {args.ticker} Cumulative to Single Quarter Conversion")
        print(f"\n- Cumulative records checked: {d['cumulative_records_checked']}")
        print(f"- Single quarter records created: {d['single_quarter_records_created']}")
        print(f"- Metrics converted: {', '.join(d['metrics_converted'])}")
        print(f"- Balance sheet skipped: {', '.join(d['balance_sheet_metrics_skipped'])}")
        if d['conversion_warnings']:
            print(f"\n## Warnings")
            for w in d['conversion_warnings']:
                print(f"- {w}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
