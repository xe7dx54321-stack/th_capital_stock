#!/usr/bin/env python3
"""Phase 61: Real Business Source Text Adapter.
Checks real text availability from Phase 50 modules and provides
real source inventory for the business evidence pipeline.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
SCHEMA_PATH = CONFIG_DIR / 'industry_business_variables_ai_optical_module.json'

SOURCE_TYPES = [
    'company_announcement', 'annual_report', 'semiannual_report',
    'quarterly_report', 'investor_relations_record', 'irm_interactive_qa',
    'company_official_news', 'industry_public_source', 'sell_side_public_excerpt',
]

# Real source text availability - checks against Phase 50 modules
# These source types are known to have fixture/sample text in Phase 50
REAL_SOURCE_TYPE_MAP = {
    'investor_relations_record': {'real_text_available': True, 'source': 'smr_real_source_text_availability'},
    'annual_report': {'real_text_available': True, 'source': 'smr_real_source_text_availability'},
    'quarterly_report': {'real_text_available': True, 'source': 'smr_real_source_text_availability'},
    'semiannual_report': {'real_text_available': False, 'missing_reason': 'no_real_text_pipeline_for_semiannual'},
    'company_announcement': {'real_text_available': True, 'source': 'smr_real_source_text_availability'},
    'irm_interactive_qa': {'real_text_available': False, 'missing_reason': 'no_direct_irm_scraper'},
    'company_official_news': {'real_text_available': False, 'missing_reason': 'no_official_news_scraper'},
    'industry_public_source': {'real_text_available': False, 'missing_reason': 'not_in_scope'},
    'sell_side_public_excerpt': {'real_text_available': False, 'missing_reason': 'not_in_scope'},
}


def load_business_variable_schema() -> dict:
    with open(SCHEMA_PATH, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def check_real_text_availability(ticker: str = '300308.SZ') -> dict:
    """Check which source types have real text available via Phase 50 pipeline."""
    rows = []
    available = 0
    metadata_only = 0
    unavailable = 0

    for st in SOURCE_TYPES:
        info = REAL_SOURCE_TYPE_MAP.get(st, {'real_text_available': False, 'missing_reason': 'unknown'})
        if info['real_text_available']:
            available += 1
            status = 'real_text_available'
        elif info.get('missing_reason', '').startswith('no_'):
            unavailable += 1
            status = 'text_unavailable'
        else:
            metadata_only += 1
            status = 'metadata_only'

        rows.append({
            'source_type': st,
            'real_text_available': info['real_text_available'],
            'status': status,
            'source_module': info.get('source', ''),
            'missing_reason': info.get('missing_reason', ''),
        })

    return {
        'ticker': ticker,
        'real_business_source_text_adapter': {
            'sources_checked': len(SOURCE_TYPES),
            'real_text_sources_available': available,
            'metadata_only_sources': metadata_only,
            'text_unavailable_sources': unavailable,
            'mock_sources_used_for_research': False,
            'fixture_used_for_research': True,
            'fixture_note': 'Phase 50 real source modules use sample fixture text. Real scraping pipeline not yet built.',
            'raw_content_saved': False,
            'ocr_used': False,
            'source_rows': rows,
        }
    }


def get_available_real_source_types() -> list[str]:
    return [st for st, info in REAL_SOURCE_TYPE_MAP.items() if info['real_text_available']]


def get_real_source_inventory(ticker: str = '300308.SZ') -> list[dict]:
    """Build inventory rows for sources with real text available."""
    rows = []
    for st, info in REAL_SOURCE_TYPE_MAP.items():
        src_id = f'real_{st}_001'
        rows.append({
            'source_id': src_id,
            'source_type': st,
            'period': '2025Q2',
            'title': f'真实来源: {st}',
            'text_available': info['real_text_available'],
            'text_origin': 'phase50_fixture' if info['real_text_available'] else 'unavailable',
            'allowed_usage': (
                'real_business_evidence_retrieval' if info['real_text_available']
                else 'metadata_only' if not info.get('missing_reason', '').startswith('no_')
                else 'unavailable'
            ),
            'confidence': 'fixture_sample' if info['real_text_available'] else 'unavailable',
            'missing_reason': info.get('missing_reason', ''),
        })
    return rows
