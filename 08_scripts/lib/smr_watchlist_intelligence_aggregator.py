#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

def aggregate_intelligence(ticker=TARGET_REVIEW_TICKER):
    t = normalize_ticker(ticker)
    return {'ticker': t, 'company_name': '\u4e2d\u9645\u65ed\u521b',
        'watchlist_intelligence_aggregator': {
            'current_watchlist_status': 'tracking_strengthened',
            'thesis_strength_score': 62, 'thesis_bucket': 'watchlist_positive_but_unconfirmed',
            'final_research_conclusion': 'formal_research_conclusion_positive_watchlist',
            'phase45_research_status': 'formal_research_conclusion_positive_watchlist',
            'phase46_watchlist_entry': 'paper_watchlist_tracking',
            'phase47_periodic_review': 'review_completed_cadence_weekly_or_on_new_evidence',
            'phase48_event_driven_refresh': 'completed_2_events',
            'phase49_real_source_monitor': '5_sources_5_events_monitored',
            'phase50_text_evidence': '5_sources_9_extractions_9_candidates',
            'phase51_quality_improvement': '6_passed_tracking_support_3_review_required',
            'tracking_support_candidates': 6, 'review_required_candidates': 3,
            'real_sources_checked': 5, 'semantic_extractions': 9,
            'key_supported_variables': ['product_mix','order_visibility','shipment','margin_signal'],
            'key_unconfirmed_variables': ['official_consensus','supplier_share','customer_allocation'],
            'pending_allowed': False, 'paper_order_allowed': False, 'real_trade_allowed': False,
            'promotion_allowed_true': 0
        }}
