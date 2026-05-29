#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables


THESIS_CLAIMS = [
    ('ai_optical_module_demand_entering_revenue', 'shipment_revenue_conversion'),
    ('high_end_product_mix_thesis_partially_supported', 'high_end_product_mix_signal'),
    ('margin_resilience_supported', 'margin_resilience'),
    ('order_visibility_partially_supported', 'order_visibility_financial_proxy'),
    ('customer_demand_strong_financial_proxy', 'customer_demand_financial_proxy'),
    ('capacity_preparation_underway', 'capacity_preparation_signal'),
    ('asp_trend_unconfirmed', 'margin_resilience'),
]


def build(conn, ticker):
    mapper = map_signals_to_industry_variables(ticker)
    rows = mapper['financial_signal_to_industry_variable_map']['rows']
    var_status = {r['industry_variable']: r for r in rows}

    result_rows = []
    for claim, var_name in THESIS_CLAIMS:
        var = var_status.get(var_name, {})
        status = var.get('variable_status', 'not_observable_from_financials')

        # Claims that are explicitly unconfirmed by design
        if 'unconfirmed' in claim:
            impact = 'unconfirmed'
        elif status in ('supported_by_financial_signal',):
            impact = 'strengthened'
        elif status == 'partially_supported':
            impact = 'partially_supported'
        elif status == 'weakened_by_financial_signal':
            impact = 'weakened'
        else:
            impact = 'unconfirmed'

        result_rows.append({
            'claim': claim,
            'impact': impact,
            'supporting_financial_variable': var_name,
            'evidence': ', '.join(var.get('supporting_financial_signals', [])[:3]),
            'limitation': ', '.join(var.get('cannot_conclude', [])[:2]),
        })

    strengthened = sum(1 for r in result_rows if r['impact'] == 'strengthened')
    partial = sum(1 for r in result_rows if r['impact'] == 'partially_supported')
    unconfirmed = sum(1 for r in result_rows if r['impact'] == 'unconfirmed')
    weakened = sum(1 for r in result_rows if r['impact'] == 'weakened')

    return {
        'ticker': ticker,
        'industry_financial_thesis_impact': {
            'claims_checked': len(result_rows),
            'claims_strengthened': strengthened,
            'claims_partially_supported': partial,
            'claims_unconfirmed': unconfirmed,
            'claims_weakened': weakened,
            'rows': result_rows,
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
        d = r['industry_financial_thesis_impact']
        print(f"# Industry Financial Thesis Impact")
        print(f"\n- Claims: {d['claims_checked']}")
        print(f"- Strengthened: {d['claims_strengthened']}")
        print(f"- Partially supported: {d['claims_partially_supported']}")
        print(f"- Unconfirmed: {d['claims_unconfirmed']}")
        for row in d['rows']:
            print(f"\n## {row['claim']}")
            print(f"- Impact: {row['impact']}")
            print(f"- Evidence: {row['evidence']}")
            print(f"- Limitation: {row['limitation']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
