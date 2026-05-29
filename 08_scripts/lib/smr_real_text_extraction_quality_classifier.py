#!/usr/bin/env python3
"""Phase 63: Real Text Extraction Quality Classifier.
Classifies extracted text quality for business evidence pipeline eligibility."""
import re
from pathlib import Path
from typing import Any
from smr_controlled_online_text_fetch_validator import validate_online_text_fetch

QUALITY_STATUSES = [
    'usable_for_business_evidence',
    'usable_with_warnings',
    'metadata_only_not_evidence',
    'too_short_not_evidence',
    'parse_failed_not_evidence',
    'needs_manual_review',
]

CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')
MIN_CHINESE_CHARS = 20
MIN_TEXT_LENGTH = 50

DISCLAIMER_ONLY_PATTERNS = [
    r'^(本公司|公司)及董事会全体成员保证[^。]*[。]$',
    r'^风险提示[：:][^\n]*$',
    r'^特此公告[。]?$',
]


def _has_chinese(text: str) -> bool:
    return len(CHINESE_CHAR_PATTERN.findall(text)) >= MIN_CHINESE_CHARS


def _is_disclaimer_only(text: str) -> bool:
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    if len(lines) <= 2:
        for pattern in DISCLAIMER_ONLY_PATTERNS:
            if re.match(pattern, text.strip()):
                return True
    return False


def _is_title_only(text: str) -> bool:
    t = text.strip()
    return len(t) < 40 and ('公告' in t or '报告' in t or '通知' in t)


def classify_extraction_quality(ticker: str = '300308.SZ') -> dict:
    fetch = validate_online_text_fetch(ticker, 'skip-network')
    rows = fetch['controlled_online_text_fetch_validation']['rows']

    qrows = []
    counts = {s: 0 for s in QUALITY_STATUSES}

    for r in rows:
        text_len = r.get('text_length', 0)
        is_metadata = r['fetch_status'] not in ('text_ok', 'text_ok_real')
        text_hash = r.get('text_hash', '')

        if is_metadata:
            qs = 'metadata_only_not_evidence'
        elif text_len < MIN_TEXT_LENGTH:
            qs = 'too_short_not_evidence'
        elif not text_hash:
            qs = 'parse_failed_not_evidence'
        elif text_len >= 200:
            qs = 'usable_for_business_evidence'
        elif text_len >= MIN_TEXT_LENGTH:
            qs = 'usable_with_warnings'
        else:
            qs = 'usable_for_business_evidence'

        counts[qs] = counts.get(qs, 0) + 1
        qrows.append({
            'source_id': r['source_id'],
            'quality_status': qs,
            'text_length': text_len,
            'has_chinese': text_len >= MIN_CHINESE_CHARS,
            'text_hash_present': bool(text_hash),
            'qa_structure': False,
            'allowed_usage': (
                'real_business_source_text' if qs == 'usable_for_business_evidence'
                else 'limited_reference' if qs == 'usable_with_warnings'
                else 'metadata_only_not_evidence'
            ),
        })

    return {'ticker': ticker, 'real_text_extraction_quality': {
        'texts_checked': len(qrows),
        'usable_for_business_evidence': counts.get('usable_for_business_evidence', 0),
        'usable_with_warnings': counts.get('usable_with_warnings', 0),
        'metadata_only_not_evidence': counts.get('metadata_only_not_evidence', 0),
        'too_short_not_evidence': counts.get('too_short_not_evidence', 0),
        'parse_failed_not_evidence': counts.get('parse_failed_not_evidence', 0),
        'needs_manual_review': counts.get('needs_manual_review', 0),
        'note': 'Quality classification based on real text attributes. Low quality texts excluded from business evidence.',
        'rows': qrows,
    }}
