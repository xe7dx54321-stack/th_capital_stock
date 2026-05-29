#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_structured_financial_data_adapter import fetch_structured_financial_data
from smr_financial_capex_field_matcher import fuzzy_match_capex_column


def build(conn, ticker):
    fetch_result = fetch_structured_financial_data(ticker, 'execute')
    records = fetch_result['structured_financial_data_fetch']['records']

    capex_records = [r for r in records if r['metric'] == 'capex']
    capex_periods = sorted(set(r['period'] for r in capex_records))

    all_columns = set()
    for r in records:
        col = r.get('column_name', r.get('raw_column_name', ''))
        if col:
            all_columns.add(col)

    matched_cols = {}
    for col in all_columns:
        is_match, method = fuzzy_match_capex_column(col)
        if is_match:
            matched_cols[col] = method

    match_conf = 'high' if len(capex_records) > 0 else 'none'
    missing = len(capex_records) == 0

    result = {
        'ticker': ticker,
        'capex_field_matching': {
            'candidate_columns_checked': len(all_columns),
            'matched_capex_columns': list(matched_cols.keys()),
            'match_methods': matched_cols,
            'capex_records_found': len(capex_records),
            'periods_covered': len(capex_periods),
            'match_confidence': match_conf,
            'capex_missing_after_match': missing,
            'notes': [],
        }
    }
    if missing:
        result['capex_field_matching']['missing_reason'] = 'capex_not_found_in_cash_flow_statement'
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ticker', default='300308.SZ')
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None, args.ticker)
    if args.markdown:
        d = r['capex_field_matching']
        print(f"# {args.ticker} Capex Field Matching Report")
        print(f"\n- Candidate columns checked: {d['candidate_columns_checked']}")
        print(f"- Matched capex columns: {len(d['matched_capex_columns'])}")
        for col in d['matched_capex_columns']:
            print(f"  - `{col}`")
        print(f"- Capex records found: {d['capex_records_found']}")
        print(f"- Periods covered: {d['periods_covered']}")
        print(f"- Match confidence: {d['match_confidence']}")
        print(f"- Still missing: {d['capex_missing_after_match']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
