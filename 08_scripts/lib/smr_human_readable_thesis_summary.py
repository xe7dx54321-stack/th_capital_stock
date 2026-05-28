#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

def build_thesis_summary(ticker=TARGET_REVIEW_TICKER):
    t = normalize_ticker(ticker)
    return {'ticker': t, 'human_thesis_summary': {
        'one_line_summary': f'{t} remains a positive watchlist case supported by product mix/order visibility/shipment evidence, but key company-specific variables remain unconfirmed.',
        'current_thesis_status': 'positive_watchlist_but_unconfirmed',
        'thesis_strength_score': 62, 'thesis_delta': 'modestly_strengthened',
        'why_continue_tracking': [
            '6 real source tracking-support candidates now support product_mix/order_visibility/shipment tracking',
            'Phase 51 quality improvement moved 6 of 9 candidates into passed_tracking_support',
            'bear case partially mitigated but not cleared',
            'sentiment/speculation edge continues to erode as the market matures'
        ],
        'why_not_pending': [
            'official consensus remains unconfirmed - cannot benchmark expectation gap',
            'supplier share remains scenario-only - cannot translate end-demand into company revenue sensitivity',
            'customer allocation remains proxy-only - no direct customer/public disclosure',
            'valuation boundary remains scenario-analysis-only - no authorized consensus to anchor range'
        ],
        'next_observation_focus': [
            'new investor relations records mentioning product mix or order visibility',
            'authorized consensus source (sell-side or company guidance)',
            'company-specific customer allocation disclosure',
            'margin signal in next quarterly/earnings report',
            'bear case worsening event (competition, price erosion, demand shift)'
        ],
        'forbidden_interpretation': ['buy_signal','target_price','position_sizing','paper_order','real_trade']
    }}
