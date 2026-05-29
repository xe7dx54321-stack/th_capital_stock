#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path:
    sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


THESIS_CLAIMS = [
    'high_end_product_mix_may_improve_revenue_quality',
    'shipment_signal_may_enter_revenue',
    'gross_margin_stability',
    'profit_elasticity',
    'cash_conversion_quality',
    'inventory_pressure',
    'expectation_gap_not_confirmed',
]


def _eval_claim(claim, signals, latest):
    ls = {s['signal']: s for s in signals if s['period'] == latest}

    if claim == 'high_end_product_mix_may_improve_revenue_quality':
        rev = ls.get('single_quarter_revenue_yoy', {})
        gm = ls.get('gross_margin', {})
        if rev.get('direction') == 'positive' and gm.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'revenue_yoy_positive_and_gross_margin_positive', 'limitation': 'cannot confirm product mix improvement from financial data alone'}
        elif rev.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'revenue_yoy_positive', 'limitation': 'gross margin not yet confirming mix improvement'}
        else:
            return {'impact': 'unjudgeable', 'evidence': 'insufficient_signal', 'limitation': 'need more periods of data'}

    if claim == 'shipment_signal_may_enter_revenue':
        rev = ls.get('single_quarter_revenue_yoy', {})
        inv = ls.get('inventory_to_revenue', {})
        cl = ls.get('contract_liabilities_yoy', {})
        if rev.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'revenue_yoy_positive', 'limitation': 'cannot confirm shipment to revenue conversion without product detail'}
        if rev.get('direction') == 'negative':
            return {'impact': 'weakened_or_unconfirmed', 'evidence': 'revenue_yoy_negative', 'limitation': 'shipment signal may not yet be reflected in revenue'}
        return {'impact': 'unjudgeable', 'evidence': 'insufficient_signal', 'limitation': 'need product-level shipment data'}

    if claim == 'gross_margin_stability':
        gm = ls.get('gross_margin', {})
        gm_delta = ls.get('gross_margin_yoy_delta', {})
        if gm_delta.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'gross_margin_yoy_delta_positive', 'limitation': 'cannot distinguish price from cost effects'}
        if gm_delta.get('direction') == 'negative':
            return {'impact': 'weakened_or_unconfirmed', 'evidence': 'gross_margin_yoy_delta_negative_or_missing', 'limitation': 'cannot directly attribute to ASP or cost changes'}
        return {'impact': 'unchanged', 'evidence': 'gross_margin_stable', 'limitation': 'no significant change detected'}

    if claim == 'profit_elasticity':
        rev = ls.get('single_quarter_revenue_yoy', {})
        np_ = ls.get('single_quarter_net_profit_yoy', {})
        nm = ls.get('net_margin', {})
        if np_.get('direction') == 'positive' and rev.get('direction') == 'positive':
            if np_.get('value', 0) > rev.get('value', 0):
                return {'impact': 'strengthened', 'evidence': 'net_profit_growth_exceeds_revenue_growth', 'limitation': 'cost structure data needed to confirm profit elasticity'}
        return {'impact': 'unjudgeable', 'evidence': 'insufficient_profit_elasticity_signal', 'limitation': 'need more detailed cost breakdown'}

    if claim == 'cash_conversion_quality':
        ocf = ls.get('operating_cash_flow_to_net_profit', {})
        if ocf.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'ocf_to_net_profit_ratio_positive', 'limitation': 'single quarter may have seasonal cash flow effects'}
        if ocf.get('direction') == 'negative':
            return {'impact': 'weakened_or_unconfirmed', 'evidence': 'ocf_to_net_profit_ratio_weak', 'limitation': 'need to check if seasonal or structural'}
        return {'impact': 'unchanged', 'evidence': 'no_strong_signal', 'limitation': 'cash conversion signal is neutral'}

    if claim == 'inventory_pressure':
        inv = ls.get('inventory_to_revenue', {})
        ar = ls.get('accounts_receivable_to_revenue', {})
        if inv.get('direction') == 'negative' or ar.get('direction') == 'negative':
            return {'impact': 'weakened_or_unconfirmed', 'evidence': 'inventory_or_receivable_pressure_detected', 'limitation': 'need to confirm if pressure is structural or cyclical'}
        if inv.get('direction') == 'positive':
            return {'impact': 'strengthened', 'evidence': 'inventory_ratio_manageable', 'limitation': 'need demand-side data to confirm'}
        return {'impact': 'unchanged', 'evidence': 'no_obvious_inventory_pressure', 'limitation': 'inventory ratio within normal range'}

    if claim == 'expectation_gap_not_confirmed':
        return {'impact': 'unjudgeable', 'evidence': 'no_market_expectation_data_available', 'limitation': 'cannot measure expectation gap without market consensus data'}

    return {'impact': 'unjudgeable', 'evidence': 'claim_not_mapped', 'limitation': 'no mapping defined'}


def build(conn, ticker):
    result = calculate_refined_quarterly_signals(ticker)
    signals_data = result['refined_quarterly_financial_signals']
    all_signals = signals_data.get('all_signals', [])
    latest = signals_data.get('latest_period', 'unknown')

    rows = []
    for claim in THESIS_CLAIMS:
        evaluation = _eval_claim(claim, all_signals, latest)
        rows.append({'claim': claim, **evaluation})

    strengthened = sum(1 for r in rows if r['impact'] == 'strengthened')
    weakened = sum(1 for r in rows if 'weakened' in r['impact'])
    unchanged = sum(1 for r in rows if r['impact'] == 'unchanged')
    unjudgeable = sum(1 for r in rows if r['impact'] == 'unjudgeable')

    return {
        'ticker': ticker,
        'financial_thesis_impact_update': {
            'claims_checked': len(rows),
            'claims_strengthened': strengthened,
            'claims_weakened': weakened,
            'claims_unchanged': unchanged,
            'claims_unjudgeable': unjudgeable,
            'latest_period': latest,
            'rows': rows,
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
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
        d = r['financial_thesis_impact_update']
        print(f"# {args.ticker} Financial Thesis Impact Update")
        print(f"\n- Claims checked: {d['claims_checked']}")
        print(f"- Strengthened: {d['claims_strengthened']}")
        print(f"- Weakened: {d['claims_weakened']}")
        print(f"- Unchanged: {d['claims_unchanged']}")
        print(f"- Unjudgeable: {d['claims_unjudgeable']}")
        print(f"\n## Claim Details")
        for row in d['rows']:
            print(f"\n### {row['claim']}")
            print(f"- Impact: {row['impact']}")
            print(f"- Evidence: {row['evidence']}")
            print(f"- Limitation: {row['limitation']}")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
