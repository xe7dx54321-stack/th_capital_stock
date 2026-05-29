#!/usr/bin/env python3
'''Evidence memory writer - writes deep evidence to stable memory.'''
import json, os, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMORY_DIR = Path(__file__).resolve().parents[2] / '09_runbooks' / 'generated' / 'evidence_memory'

def _now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def _make_id(ticker: str, var: str, idx: int) -> str:
    h = hashlib.sha256(f'{ticker}:{var}:{idx}'.encode()).hexdigest()[:8]
    return f'em_{ticker.replace(".","_")}_{h}'

def write_evidence_memory(ticker: str, deep_evidence: list[dict],
                          company_name: str = '', industry: str = '',
                          dry_run: bool = False) -> dict[str, Any]:
    '''Write deep evidence records to evidence memory.'''
    schema_path = Path(__file__).resolve().parents[2] / 'config' / 'evidence_memory_schema.json'
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    written = 0
    skipped = 0
    duplicates = 0
    records = []
    seen_ids = set()
    now = _now()

    for i, ev in enumerate(deep_evidence):
        var = ev.get('business_variable', '')
        eid = ev.get('evidence_id', _make_id(ticker, var, i))
        if eid in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(eid)

        cc = ev.get('cannot_conclude', [])
        if isinstance(cc, str):
            cc = [cc]

        rec = {
            'evidence_id': eid,
            'ticker': ticker,
            'company_name': company_name,
            'industry': industry,
            'phase_source': 'phase67b',
            'source_id': ev.get('source_id', ''),
            'source_type': ev.get('source_type', ''),
            'source_title': ev.get('title', ev.get('source_title', '')),
            'publish_date': ev.get('publish_date', ''),
            'pdf_url_hash_or_source_url_hash': ev.get('span_location_hash', ''),
            'text_hash': ev.get('text_hash', ''),
            'quoted_span': ev.get('quoted_span', ''),
            'span_location_or_hash': ev.get('span_location_hash', ''),
            'business_variable': var,
            'claim_type': ev.get('claim_type', var + '_supported'),
            'evidence_strength': ev.get('evidence_strength', 'business_context'),
            'confidence': ev.get('confidence', 'low'),
            'quality_grade': ev.get('quality_grade', ''),
            'limitation': ev.get('limitation', ''),
            'cannot_conclude': cc,
            'keywords_hit': ev.get('keywords_hit', []),
            'allowed_usage': 'brief_support' if ev.get('evidence_strength') != 'review_required' else 'review_required_only',
            'requires_human_review': ev.get('requires_human_review', False),
            'review_status': 'review_required' if ev.get('requires_human_review') else 'none',
            'created_at': now,
            'updated_at': now
        }
        records.append(rec)

    if not dry_run:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        out_path = MEMORY_DIR / f'evidence_memory_{ticker.replace(".","_")}.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'schema_version': '1.0', 'ticker': ticker,
                       'records': records, 'total': len(records),
                       'created_at': now}, f, ensure_ascii=False, indent=2)

    return {
        'ticker': ticker,
        'source_phase': 'phase67b',
        'input_deep_evidence': len(deep_evidence),
        'records_written': len(records) if not dry_run else len(records),
        'records_skipped': skipped,
        'duplicate_records': duplicates,
        'memory_path': str(MEMORY_DIR) if not dry_run else str(MEMORY_DIR) + ' (dry_run)',
        'memory_path_ignored': True,
        'mock_used': False,
        'fixture_used': False,
        'pending_created': 0,
        'paper_order_created': 0,
        'real_trade_created': 0
    }
