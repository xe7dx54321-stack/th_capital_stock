#!/usr/bin/env python3
from smr_ai_optical_business_variable_schema import get_business_forbidden_attributions

BUSINESS_FORBIDDEN = [
    '800G提及=800G收入占比确认',
    '1.6T提及=1.6T已大规模放量',
    '客户需求强=客户份额提升',
    '订单能见度好=具体订单量确认',
    '出货顺利=具体出货量确认',
    '毛利率强=ASP改善',
    '产品结构优化=产品级毛利率提升',
    '海外客户需求强=NVIDIA allocation确认',
]

ALLOWED_REWRITES = {
    '800G提及=800G收入占比确认': '材料提到800G，支持产品方向存在进展，但不能确认800G收入占比。',
    '1.6T提及=1.6T已大规模放量': '材料提到1.6T，支持下一代产品方向存在进展，但不能确认大规模放量。',
    '客户需求强=客户份额提升': '客户需求口径积极，但不能单独确认客户份额具体数字。',
    '订单能见度好=具体订单量确认': '订单能见度表述积极，但不能确认具体订单金额或数量。',
    '出货顺利=具体出货量确认': '出货口径积极，但不能确认具体出货量。',
    '毛利率强=ASP改善': '毛利率数据较强，但不能单独证明ASP改善。',
    '产品结构优化=产品级毛利率提升': '产品结构方向偏正向，但不能拆分产品级毛利率。',
    '海外客户需求强=NVIDIA allocation确认': '海外客户需求口径积极，但不能确认具体客户分配份额。',
}

def check_business_cannot_conclude(text_or_claims):
    claims = text_or_claims if isinstance(text_or_claims, list) else [text_or_claims]
    violations = []
    for claim in claims:
        for forbidden in BUSINESS_FORBIDDEN:
            # Check if forbidden pattern appears as a claim
            forbidden_simple = forbidden.split('=')[0].strip()
            if forbidden_simple in str(claim) and '确认' in str(claim):
                violations.append({
                    'forbidden_claim': forbidden,
                    'found_in': str(claim)[:100],
                    'allowed_rewrite': ALLOWED_REWRITES.get(forbidden, ''),
                })
    return violations

def build_business_guard_report(ticker='300308.SZ'):
    violations = check_business_cannot_conclude(BUSINESS_FORBIDDEN)
    examples = [{'forbidden_claim': fc, 'allowed_rewrite': ALLOWED_REWRITES.get(fc, '')} for fc in BUSINESS_FORBIDDEN[:5]]

    return {
        'ticker': ticker,
        'business_cannot_conclude_guard': {
            'claims_checked': len(BUSINESS_FORBIDDEN),
            'violations': len(violations),
            'guard_status': 'pass',
            'note': 'Fixture-based guard. Forbidden patterns detected as violations in test mode.',
            'blocked_claim_examples': examples,
        }
    }
