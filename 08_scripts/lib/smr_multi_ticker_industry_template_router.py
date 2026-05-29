#!/usr/bin/env python3
'''Multi-ticker industry template router.'''
import sys
from pathlib import Path
from typing import Any

AI_OPTICAL_VARS = ['800G_product_signal','1_6T_product_signal','high_end_product_mix','shipment_delivery_signal','customer_demand_signal','order_visibility_signal','asp_price_signal','capacity_expansion_signal']
GENERIC_HARD_TECH_VARS = ['revenue_growth_signal','gross_margin_signal','rd_investment_signal','customer_demand_signal','capacity_expansion_signal','order_visibility_signal','product_roadmap_signal','competitive_position_signal']

def route_industry_template(ticker: str) -> dict[str, Any]:
    from smr_multi_ticker_universe import get_ticker_config
    cfg = get_ticker_config(ticker)
    template = cfg.get('industry_template', 'unknown_or_missing')
    if template == 'ai_optical_module':
        return {'industry_template': template, 'business_variables': AI_OPTICAL_VARS, 'template_available': True}
    elif template == 'generic_hard_tech':
        return {'industry_template': template, 'business_variables': GENERIC_HARD_TECH_VARS, 'template_available': True}
    else:
        return {'industry_template': 'unknown_or_missing', 'business_variables': [], 'template_available': False, 'failure_reason': 'no_industry_template_configured'}

def route_all() -> dict[str, Any]:
    from smr_multi_ticker_universe import load_universe
    u = load_universe()
    tickers = [t['ticker'] for t in u.get('tickers', [])]
    rows = []
    for t in tickers:
        r = route_industry_template(t)
        r['ticker'] = t
        rows.append(r)
    return {'tickers_checked': len(tickers), 'template_routed': sum(1 for r in rows if r.get('template_available')), 'rows': rows}
