#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker

DECISIONS = ['continue_tracking','pause_tracking','archive_candidate','request_research_revalidation','request_more_real_source_text','request_manual_review','unknown']

def classify_decision(tracking_support_count=6, review_required_count=3, thesis_score=62):
    if tracking_support_count > 0 and review_required_count > 0:
        decision = 'continue_tracking'; confidence = 'medium'
    elif tracking_support_count == 0 and review_required_count > 0:
        decision = 'request_more_real_source_text'; confidence = 'low'
    elif tracking_support_count > 0 and review_required_count == 0:
        decision = 'request_research_revalidation'; confidence = 'medium'
    else:
        decision = 'unknown'; confidence = 'low'
    return {'decision': decision, 'decision_confidence': confidence,
        'decision_reason': _build_reason(decision, tracking_support_count, review_required_count),
        'allowed_next_actions': _allowed(decision),
        'forbidden_next_actions': ['create_pending','create_paper_order','create_trade','issue_buy_signal','issue_sell_signal']}

def _build_reason(d, ts, rr):
    reasons = []
    if ts > 0: reasons.append(f'{ts} tracking-support candidates now support continued tracking')
    if rr > 0: reasons.append(f'{rr} review-required sensitive variable candidates still block pending')
    reasons.append('thesis remains positive but unconfirmed')
    return reasons

def _allowed(d):
    return {
        'continue_tracking': ['continue_watchlist_tracking','monitor_next_events','request_more_real_source_text','review_sensitive_candidates'],
        'request_more_real_source_text': ['request_real_source_text_extraction','monitor_source_metadata'],
        'request_research_revalidation': ['research_revalidation','event_driven_revalidation'],
    }.get(d, ['manual_review'])

def build_decision(ticker=TARGET_REVIEW_TICKER, tracking_support=6, review_required=3):
    d = classify_decision(tracking_support, review_required)
    return {'ticker': normalize_ticker(ticker), 'tracking_decision': d}
