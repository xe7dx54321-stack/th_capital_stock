#!/usr/bin/env python3
from smr_real_financial_source_registry import load_registry

def check_real_source_availability(ticker='300308.SZ'):
    registry = load_registry()
    sources = registry.get('sources', [])
    real_sources = [s for s in sources if s.get('confidence') == 'real_structured']
    fallback_sources = [s for s in sources if s.get('confidence') == 'real_report_text_extracted']
    real_available = any(s.get('status') == 'available' for s in real_sources)
    preferred = registry.get('preferred_primary', '')
    result = {'ticker': ticker, 'real_financial_source_availability': {
        'sources_checked': len(sources),
        'real_structured_available': real_available,
        'report_text_fallback_available': any(s.get('status', '') == 'fallback' for s in fallback_sources),
        'fixture_available': True,
        'preferred_source': preferred if real_available else 'manual_financial_fixture',
        'real_data_available': real_available,
        'reason': '' if real_available else 'no_real_financial_source_configured',
        'availability_rows': real_sources,
        'note': 'Source availability does not guarantee data fetch success.'
    }}
    return result
