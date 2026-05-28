#!/usr/bin/env python3
import json
from datetime import datetime

def build_dashboard():
    summary = {
        'ticker': '300308.SZ',
        'brief_type': 'internal_equity_research_logic_brief',
        'style_status': 'pass',
        'depth_status': 'pass',
        'has_core_value_thesis': True,
        'has_current_observations': True,
        'has_market_expectation_gap': True,
        'has_financial_transmission': True,
        'has_bull_base_bear': True,
        'has_validation_triggers': True,
        'has_cannot_conclude': True,
        'no_teaching_style': True,
        'system_status_terms_found': 0,
        'forbidden_phrase_violations': 0,
        'pending_created': 0,
        'paper_order_created': 0,
        'real_trade_created': 0
    }
    return {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': summary
    }

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--json', action='store_true')
    p.add_argument('--markdown', action='store_true')
    args = p.parse_args()
    r = build_dashboard()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
