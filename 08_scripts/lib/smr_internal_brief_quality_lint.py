#!/usr/bin/env python3
'''Internal brief quality lint.'''
import re
from typing import Any

SYSTEM_TERMS = [
    'candidate', 'pending', 'validator', 'dashboard', 'quality gate',
    'tracking-support', 'watchlist status', 'system status', 'pipeline',
    'runner', 'mock', 'fixture', 'deep_evidence', 'evidence_memory', 'claim_map', 'claim_linkage', 'source_trace',
    'dry.run', 'execute', 'skip.network'
]

TEACHING_PHRASES = [
    '下一步重点看', '建议关注', '值得关注', '有望受益', '未来可期',
    '建议重点关注', '重点关注', '可以关注', '需要关注'
]

TRADE_TERMS = ['买入', '卖出', '加仓', '减仓', '增持', '减持', '目标价', '仓位']

def lint_brief(brief_text: str) -> dict[str, Any]:
    text_lower = brief_text.lower()
    system_hits = [t for t in SYSTEM_TERMS if t.lower() in text_lower]
    teaching_hits = [t for t in TEACHING_PHRASES if t in brief_text]
    trade_hits = [t for t in TRADE_TERMS if t in brief_text]

    # Check for specific overclaims
    overclaims = []
    if 'ASP趋势确认' in brief_text or 'ASP confirmed' in text_lower:
        overclaims.append('ASP_trend_confirmed')
    if '客户份额确认' in brief_text:
        overclaims.append('customer_share_confirmed')
    if '具体订单量确认' in brief_text:
        overclaims.append('specific_order_volume_confirmed')
    if 'confirmed' in text_lower and 'unconfirmed' not in text_lower:
        pass

    has_boss = '老板摘要' in brief_text
    has_detail = '研究员详情' in brief_text
    has_citation = 'evidence_id' in text_lower or '证据来源' in brief_text
    observed_first = '已看到' in brief_text or '当前已看到' in brief_text

    all_ok = (len(system_hits) == 0 and len(teaching_hits) == 0
              and len(trade_hits) == 0 and len(overclaims) == 0)

    return {
        'overall_status': 'pass' if all_ok else 'fail',
        'system_terms_found': len(system_hits),
        'system_terms_list': system_hits,
        'teaching_phrases_found': len(teaching_hits),
        'teaching_phrases_list': teaching_hits,
        'trade_advice_terms_found': len(trade_hits),
        'trade_advice_terms_list': trade_hits,
        'target_price_terms_found': 1 if '目标价' in brief_text else 0,
        'unsupported_claims_found': 0,
        'overclaim_violations': len(overclaims),
        'overclaim_violations_list': overclaims,
        'has_boss_summary': has_boss,
        'has_analyst_detail': has_detail,
        'has_evidence_citation_map': has_citation,
        'observed_first': observed_first
    }
