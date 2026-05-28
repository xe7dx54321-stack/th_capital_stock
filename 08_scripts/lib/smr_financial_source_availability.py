#!/usr/bin/env python3
from __future__ import annotations

SOURCE_TYPES = ['structured_financial_db','cninfo_financial_report','annual_report_text','quarterly_report_text','semiannual_report_text','earnings_flash','earnings_preview','manual_financial_fixture','source_unavailable']

def check_financial_source_availability(ticker='300308.SZ'):
    sources = [
        {'source_type': 'structured_financial_db', 'source_status': 'unavailable', 'period': '待取得', 'raw_content_saved': False, 'allowed_next_action': 'no_action_possible'},
        {'source_type': 'quarterly_report_text', 'source_status': 'available_or_fixture', 'period': '待取得', 'raw_content_saved': False, 'allowed_next_action': 'extract_financial_metrics'},
        {'source_type': 'annual_report_text', 'source_status': 'available_or_fixture', 'period': '待取得', 'raw_content_saved': False, 'allowed_next_action': 'extract_financial_metrics'},
        {'source_type': 'manual_financial_fixture', 'source_status': 'available', 'period': '2024Q4/2025Q1/2025Q2', 'raw_content_saved': False, 'allowed_next_action': 'use_fixture_for_framework_test'},
        {'source_type': 'earnings_flash', 'source_status': 'available_or_fixture', 'period': '待取得', 'raw_content_saved': False, 'allowed_next_action': 'extract_financial_metrics'}
    ]
    available = [s for s in sources if s['source_status'] != 'unavailable']
    missing = [s for s in sources if s['source_status'] == 'unavailable']
    return {'ticker': ticker, 'financial_source_availability': {
        'sources_checked': len(sources),
        'structured_data_available': False,
        'financial_report_text_available': True,
        'manual_fixture_available': True,
        'latest_period_detected': '待取得',
        'source_rows': sources,
        'missing_sources': [s['source_type'] for s in missing],
        'note': 'Source availability does not equal data availability. Fixture data does not equal real financial data.'
    }}
