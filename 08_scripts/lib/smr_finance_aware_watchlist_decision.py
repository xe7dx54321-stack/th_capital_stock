#!/usr/bin/env python3
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review


def make_finance_aware_watchlist_decision(ticker='300308.SZ'):
    review = run_finance_aware_thesis_review(ticker)
    rd = review['finance_aware_thesis_review']

    strengthened = rd['claims_strengthened']
    unconfirmed = rd['claims_unconfirmed']
    weakened = rd['claims_weakened']

    # Decision logic
    if weakened >= 3:
        decision = 'pause_tracking_financials_weakened'
        confidence = 'medium'
    elif strengthened >= 3 and unconfirmed >= 2:
        decision = 'continue_tracking_financials_strengthened'
        confidence = 'medium'
    elif strengthened >= 1:
        decision = 'continue_tracking_financials_strengthened'
        confidence = 'medium'
    elif strengthened == 0 and unconfirmed > 0:
        decision = 'continue_tracking_key_gaps_unconfirmed'
        confidence = 'low'
    else:
        decision = 'continue_tracking_financials_mixed'
        confidence = 'low'

    reasons = []
    if strengthened > 0:
        reasons.append('真实财务数据支持收入和利润端增强')
        reasons.append('毛利率水平对利润质量形成支撑')
    if unconfirmed > 0:
        reasons.append('客户份额、ASP、产品代际和预期差仍未确认')
    if weakened > 0:
        reasons.append('部分财务变量出现弱化信号')

    return {
        'ticker': ticker,
        'finance_aware_watchlist_decision': {
            'decision': decision,
            'decision_confidence': confidence,
            'decision_reason': reasons,
            'watchlist_state_change': (
                'strengthened_research_support' if strengthened > 0 else 'no_significant_change'
            ),
            'forbidden_actions': [
                'create_pending',
                'create_paper_order',
                'create_trade',
                'issue_buy_signal',
            ],
            'pending_created': 0,
            'paper_order_created': 0,
            'real_trade_created': 0,
        }
    }
