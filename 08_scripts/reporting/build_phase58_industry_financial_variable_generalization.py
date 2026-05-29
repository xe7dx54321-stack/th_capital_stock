#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def build(conn, ticker=None):
    return {
        'phase': 'phase58',
        'industry_financial_variable_generalization': {
            'generic_financial_framework': [
                'revenue_growth',
                'profit_growth',
                'gross_margin',
                'cash_conversion',
                'inventory',
                'receivables',
                'capex',
            ],
            'industry_specific_template': [
                'high_end_product_mix_signal',
                'shipment_revenue_conversion',
                'margin_resilience',
                'order_visibility_financial_proxy',
                'customer_demand_financial_proxy',
                'capacity_preparation_signal',
            ],
            'ticker_specific_application': [
                '300308.SZ AI optical module thesis mapping',
            ],
            'not_assumed_to_generalize': [
                'AI optical module variables to non-optical industries',
                '300308 thesis impact to all optical module companies',
                'financial signal as direct proof of product/customer/ASP',
            ],
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build(None)
    if args.markdown:
        d = r['industry_financial_variable_generalization']
        print('# Industry Financial Variable Generalization')
        print('\n## Generic Financial Framework')
        for c in d['generic_financial_framework']:
            print(f'- {c}')
        print('\n## Industry-Specific Template (AI Optical Module)')
        for c in d['industry_specific_template']:
            print(f'- {c}')
        print('\n## Ticker-Specific Application')
        for c in d['ticker_specific_application']:
            print(f'- {c}')
        print('\n## NOT Assumed to Generalize')
        for c in d['not_assumed_to_generalize']:
            print(f'- {c}')
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
