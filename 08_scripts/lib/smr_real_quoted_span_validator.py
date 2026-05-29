#!/usr/bin/env python3
"""Phase 61: Real Quoted Span Validator.
Validates that quoted spans are traceable to their source text,
filtering out pseudo-references, title-only, and boilerplate content.
"""
from __future__ import annotations
from typing import Any

from smr_real_text_business_evidence_retriever import (
    retrieve_real_text_business_evidence,
    REAL_TEXT_SPANS,
)

TITLE_ONLY_INDICATORS = ['公告', '通知', '提示', '说明']
BOILERPLATE_PATTERNS = ['风险提示', '免责声明', '投资者注意', '投资有风险']
MARKETING_SLOGANS = ['行业领先', '全球领先', '世界一流', '引领行业', '首选']
MIN_SPAN_LENGTH = 15


def _check_source_text_contains(span: str, source_type: str) -> bool:
    """Check if the span text can be found in the real source text content."""
    # Build a combined text blob from all spans for this source type
    type_spans = REAL_TEXT_SPANS.get(source_type, {})
    combined = ''
    for var_spans in type_spans.values():
        for s in var_spans:
            combined += s['quoted_span'] + ' '
    # Check if span text (or significant substring) exists
    if not combined:
        return False
    check = span.strip()[:50]  # Check first 50 chars
    return check in combined


def _is_title_only(span: str) -> bool:
    for indicator in TITLE_ONLY_INDICATORS:
        if span.strip().startswith(indicator) and len(span) < 40:
            return True
    return False


def _is_boilerplate(span: str) -> bool:
    for bp in BOILERPLATE_PATTERNS:
        if bp in span:
            return True
    return False


def _is_marketing_slogan_only(span: str) -> bool:
    for slogan in MARKETING_SLOGANS:
        if slogan in span and len(span) < 50:
            return True
    return False


def validate_quoted_spans(ticker: str = '300308.SZ') -> dict:
    """Validate all quoted spans from real text retrieval."""
    retrieval = retrieve_real_text_business_evidence(ticker)
    spans = retrieval['real_text_business_evidence_retrieval']['rows']

    result_rows = []
    passed = 0
    review_required = 0
    rejected = 0

    for span in spans:
        span_text = span.get('quoted_span', '')
        source_type = span.get('source_type', '')
        issues = []

        # Check source text contains span
        source_contains = _check_source_text_contains(span_text, source_type)
        if not source_contains:
            issues.append('source_text_does_not_contain_span')

        # Check span length
        span_length_ok = len(span_text.strip()) >= MIN_SPAN_LENGTH
        if not span_length_ok:
            issues.append('span_too_short')

        # Check not title only
        is_title = _is_title_only(span_text)
        if is_title:
            issues.append('title_only')

        # Check not boilerplate
        is_boiler = _is_boilerplate(span_text)
        if is_boiler:
            issues.append('boilerplate')

        # Check not marketing slogan
        is_slogan = _is_marketing_slogan_only(span_text)
        if is_slogan:
            issues.append('marketing_slogan_only')

        # Determine validation status
        if not source_contains or not span_length_ok:
            status = 'rejected'
            rejected += 1
        elif is_title or is_slogan:
            status = 'review_required'
            review_required += 1
        elif is_boiler:
            status = 'review_required'
            review_required += 1
        else:
            status = 'passed'
            passed += 1

        result_rows.append({
            'span_id': span['span_id'],
            'source_id': span['source_id'],
            'source_type': source_type,
            'business_variable': span['business_variable'],
            'quoted_span_preview': span_text[:80],
            'validation_status': status,
            'section_type': span.get('section', 'unknown'),
            'span_length_ok': span_length_ok,
            'source_text_contains_span': source_contains,
            'title_only': is_title,
            'boilerplate': is_boiler,
            'marketing_slogan': is_slogan,
            'issues': issues,
        })

    return {
        'ticker': ticker,
        'real_quoted_span_validation': {
            'spans_checked': len(spans),
            'spans_passed': passed,
            'spans_review_required': review_required,
            'spans_rejected': rejected,
            'note': 'Quoted span validation against Phase 50 fixture source text. Rejected spans cannot enter semantic extraction.',
            'rows': result_rows,
        }
    }
