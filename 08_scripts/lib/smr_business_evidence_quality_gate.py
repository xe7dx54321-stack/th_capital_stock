#!/usr/bin/env python3
from smr_semantic_business_evidence_extractor import extract_semantic_business_evidence

GENERIC_PHRASES = ['需求旺盛', '前景广阔', '行业领先', '技术领先', '市场广阔']
TITLE_ONLY_INDICATORS = ['公告', '通知', '提示', '说明']

def run_business_evidence_quality_gate(ticker='300308.SZ'):
    evidence = extract_semantic_business_evidence(ticker)
    rows = evidence['semantic_business_evidence']['rows']

    qg_rows = []
    passed = 0; review = 0; rejected = 0

    for ev in rows:
        span = ev['quoted_span']
        issues = []

        # Check source traceability
        if not ev.get('source_id'):
            issues.append('no_source_traceability')

        # Check quoted span
        if len(span) < 10:
            issues.append('quoted_span_too_short')

        # Title-only check
        is_title = any(ind in span[:4] for ind in TITLE_ONLY_INDICATORS)
        if is_title:
            issues.append('appears_title_only')

        # Generic language check
        if any(gp in span for gp in GENERIC_PHRASES) and len(span) < 30:
            issues.append('potentially_generic_language')

        # Determine quality status
        if 'no_source_traceability' in issues or 'quoted_span_too_short' in issues:
            quality_status = 'rejected'
            rejected += 1
        elif ev.get('sensitive_variable') and ev.get('evidence_strength') != 'strong_direct_evidence':
            quality_status = 'review_required'
            review += 1
        elif 'appears_title_only' in issues:
            quality_status = 'review_required'
            review += 1
        elif issues:
            quality_status = 'review_required'
            review += 1
        else:
            quality_status = 'passed'
            passed += 1

        qg_rows.append({
            'evidence_id': ev['evidence_id'],
            'quality_status': quality_status,
            'issues': issues,
            'allowed_usage': (
                'business_judgment_support' if quality_status == 'passed'
                else 'limited_reference_only' if quality_status == 'review_required'
                else 'not_allowed'
            ),
            'blocked_usages': [
                'confirmed_customer_share', 'confirmed_ASP',
                'confirmed_order_volume', 'confirmed_product_mix_percentage'
            ] if ev.get('sensitive_variable') else [],
        })

    return {
        'ticker': ticker,
        'business_evidence_quality_gate': {
            'evidence_checked': len(rows),
            'passed': passed,
            'review_required': review,
            'rejected': rejected,
            'note': 'Fixture-based quality gate. Sensitive variables flagged for review. Generic language filtered.',
            'rows': qg_rows,
        }
    }
