#!/usr/bin/env python3
"""Phase 62: Chinese Text Normalizer.
Normalizes fetched Chinese business text: whitespace, Q&A structure, disclaimer removal.
"""
from __future__ import annotations
import re, hashlib
from pathlib import Path
from typing import Any
from smr_controlled_chinese_text_fetcher import fetch_controlled_chinese_texts

DISCLAIMER_PATTERNS = [
    r'本公司及董事会全体成员保证信息披露[^。\n]*[。\n]',
    r'风险提示[：:][^\n]*',
    r'免责声明[：:][^\n]*',
    r'投资者注意[：:][^\n]*',
    r'投资有风险[^\n]*',
    r'本公告[^。]*仅供参考[^。]*[。]',
    r'特此[公告|说明|提示][。]?',
]

QA_PATTERNS = [
    (r'问题[一二三四五六七八九十\d]+[：:、.．]\s*', 'Q: '),
    (r'Q[：:]\s*', 'Q: '),
    (r'投资者提问[：:]\s*', 'Q: '),
    (r'[回答][：:答]\s*', 'A: '),
    (r'A[：:]\s*', 'A: '),
    (r'公司答复[：:]\s*', 'A: '),
    (r'回复[：:]\s*', 'A: '),
]


def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def _remove_disclaimers(text: str) -> tuple[str, int]:
    removed = 0
    for pattern in DISCLAIMER_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            removed += len(matches)
            text = re.sub(pattern, '', text)
    return text, removed


def _detect_qa_structure(text: str) -> bool:
    q_count = len(re.findall(r'(问题[一二三四五六七八九十\d]+|Q[：:]|投资者提问)', text))
    a_count = len(re.findall(r'([回答][：:答]|A[：:]|公司答复)', text))
    return q_count >= 1 and a_count >= 1


def _normalize_whitespace(text: str) -> str:
    # Collapse multiple newlines and spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()
    return text


def normalize_chinese_texts(ticker: str = '300308.SZ') -> dict:
    fetch_result = fetch_controlled_chinese_texts(ticker, mode='skip-network')
    text_rows = [r for r in fetch_result['controlled_chinese_text_fetch']['rows']
                 if r['fetch_status'] in ('text_ok', 'text_ok_real')]

    rows = []
    normalized_count = 0
    too_short = 0
    qa_detected = 0
    disclaimer_removed = 0

    for tr in text_rows:
        text = tr.get('text_preview', '')
        if not text or len(text) < 30:
            too_short += 1
            rows.append({
                'source_id': tr['source_id'],
                'original_text_length': len(text or ''),
                'normalized_text_length': 0,
                'qa_structure_detected': False,
                'disclaimers_removed': 0,
                'status': 'too_short',
            })
            continue

        # Remove disclaimers
        clean_text, disc_count = _remove_disclaimers(text)
        disclaimer_removed += disc_count

        # Detect Q&A structure
        is_qa = _detect_qa_structure(clean_text)
        if is_qa:
            qa_detected += 1

        # Normalize whitespace
        normalized_text = _normalize_whitespace(clean_text)

        if len(normalized_text) < 50:
            too_short += 1
            rows.append({
                'source_id': tr['source_id'],
                'original_text_length': len(text),
                'normalized_text_length': len(normalized_text),
                'qa_structure_detected': is_qa,
                'disclaimers_removed': disc_count,
                'status': 'too_short_after_normalization',
            })
        else:
            normalized_count += 1
            rows.append({
                'source_id': tr['source_id'],
                'source_type': tr['source_type'],
                'original_text_length': len(text),
                'normalized_text_length': len(normalized_text),
                'normalized_text_hash': _compute_hash(normalized_text),
                'qa_structure_detected': is_qa,
                'disclaimers_removed': disc_count,
                'status': 'normalized',
                'normalized_text_preview': normalized_text[:300],
            })

    return {
        'ticker': ticker,
        'chinese_text_normalization': {
            'texts_checked': len(text_rows),
            'normalized': normalized_count,
            'too_short': too_short,
            'qa_structure_detected': qa_detected,
            'disclaimer_removed': disclaimer_removed,
            'note': 'Text normalization only cleans formatting. Does not rewrite factual content.',
            'rows': rows,
        }
    }
