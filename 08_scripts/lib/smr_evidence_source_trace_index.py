#!/usr/bin/env python3
'''Evidence source trace index.'''
from typing import Any

TRACE_QUALITY = ['high_traceability', 'medium_traceability', 'low_traceability', 'trace_failed']

def build_source_trace_index(evidence_records: list[dict]) -> dict[str, Any]:
    results = []
    counts = {q: 0 for q in TRACE_QUALITY}
    for ev in evidence_records:
        has_sid = bool(ev.get('source_id'))
        has_txt = bool(ev.get('text_hash'))
        has_span = bool(ev.get('span_location_or_hash') or ev.get('quoted_span'))
        score = sum([has_sid, has_txt, has_span])
        if score >= 3: tq = 'high_traceability'
        elif score >= 2: tq = 'medium_traceability'
        elif score >= 1: tq = 'low_traceability'
        else: tq = 'trace_failed'
        counts[tq] += 1
        results.append({
            'evidence_id': ev.get('evidence_id', ''),
            'source_id': ev.get('source_id', ''),
            'source_type': ev.get('source_type', ''),
            'source_title': ev.get('source_title', ''),
            'publish_date': ev.get('publish_date', ''),
            'pdf_url_hash_or_source_url_hash': ev.get('pdf_url_hash_or_source_url_hash', ''),
            'text_hash': ev.get('text_hash', ''),
            'quoted_span_hash': ev.get('span_location_or_hash', ''),
            'span_location_or_hash': ev.get('span_location_or_hash', ''),
            'source_trace_status': 'traceable' if tq != 'trace_failed' else 'not_traceable',
            'trace_quality': tq
        })
    return {
        'evidence_records_checked': len(evidence_records),
        'high_traceability': counts['high_traceability'],
        'medium_traceability': counts['medium_traceability'],
        'low_traceability': counts['low_traceability'],
        'trace_failed': counts['trace_failed'],
        'trace_status': 'pass' if counts['trace_failed'] == 0 else 'partial_fail',
        'rows': results
    }
