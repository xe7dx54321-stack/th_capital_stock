#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts
from smr_quoted_span_validator import validate_span
from smr_source_traceability_scoring import score_traceability

SENSITIVE_VARS = {'supplier_share_scenario', 'customer_allocation_proxy', 'official_consensus_status'}

def calibrate_candidate(candidate):
    span_result = validate_span(candidate)
    trace_result = score_traceability(candidate)
    span_status = span_result['span_status']
    is_sensitive = candidate.get('variable', '') in SENSITIVE_VARS
    span_strong = span_status == 'passed'
    span_ok = span_status in ('passed', 'downgraded')
    trace_ok = trace_result['traceability_bucket'] in ('high', 'medium')

    if is_sensitive:
        status = 'review_required'
    elif span_strong:
        # Strong quoted_span can compensate for lower traceability (fixture sources)
        status = 'passed_tracking_support'
    elif span_ok and trace_ok:
        status = 'downgraded_context_only'
    else:
        status = 'review_required'

    upgrade_reasons = []
    if status == 'passed_tracking_support':
        if span_strong: upgrade_reasons.append('quoted_span_passed')
        if trace_ok: upgrade_reasons.append('traceability_medium_or_better')
        if not trace_ok: upgrade_reasons.append('span_strong_compensates_traceability')

    return {'candidate_id': candidate.get('candidate_id'), 'variable': candidate.get('variable'),
            'quality_status_before': 'downgraded', 'quality_status_after': status,
            'final_allowed_usage': 'research_tracking_support',
            'upgrade_reason': upgrade_reasons,
            'confirmation_status': 'candidate_not_confirmed',
            'usable_for_promotion': False}

def build_calibration(candidates, ticker=TARGET_REVIEW_TICKER):
    rows = [calibrate_candidate(c) for c in candidates]
    statuses = {}
    for r in rows: statuses[r['quality_status_after']] = statuses.get(r['quality_status_after'], 0) + 1
    return {'ticker': normalize_ticker(ticker), 'quality_gate_calibration': {
        'candidates_checked': len(candidates),
        'passed_tracking_support': statuses.get('passed_tracking_support', 0),
        'downgraded_context_only': statuses.get('downgraded_context_only', 0),
        'review_required': statuses.get('review_required', 0),
        'rejected': statuses.get('rejected', 0),
        'usable_for_promotion_true': 0, 'confirmed_variables_added': 0,
        'rows': rows
    }}
