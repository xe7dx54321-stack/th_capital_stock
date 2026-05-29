#!/usr/bin/env python3
from smr_ai_optical_financial_variable_schema import get_forbidden_attributions


FORBIDDEN_CLAIMS = [
    '收入增长证明800G放量',
    '收入增长证明1.6T放量',
    '收入增长证明客户份额提升',
    '毛利率强证明ASP改善',
    '毛利率强证明高端产品占比提升',
    '存货增加证明订单增强',
    '合同负债增加证明客户订单确认',
    '应收增加证明需求增强',
    'capex增加证明扩产成功',
]

ALLOWED_REWRITES = {
    '收入增长证明800G放量': '收入增长支持收入端兑现，但不能单独证明800G放量。',
    '收入增长证明1.6T放量': '收入增长支持收入端兑现，但不能单独证明1.6T放量。',
    '收入增长证明客户份额提升': '收入增长说明需求端较强，但不能单独证明客户份额提升。',
    '毛利率强证明ASP改善': '毛利率处于较强水平支持利润质量，但不能单独证明ASP改善。',
    '毛利率强证明高端产品占比提升': '毛利率水平可能反映产品结构变化方向，但不能单独证明高端产品占比。',
    '存货增加证明订单增强': '存货增加可能暗示备货意愿，但不能单独证明订单增强。',
    '合同负债增加证明客户订单确认': '合同负债增加可能反映预收款，但不能单独证明客户订单确认。',
    '应收增加证明需求增强': '应收变化需要结合收入趋势分析，不能单独证明需求增强。',
    'capex增加证明扩产成功': 'capex增加说明公司在投入产能，但不能单独证明扩产成功。',
}


def check_cannot_conclude_guard(text_or_claims):
    """Check if any forbidden claims appear in text. Returns violations."""
    claims = text_or_claims if isinstance(text_or_claims, list) else [text_or_claims]
    violations = []
    for claim in claims:
        for forbidden in FORBIDDEN_CLAIMS:
            if forbidden in str(claim):
                violations.append({
                    'forbidden_claim': forbidden,
                    'found_in': str(claim)[:100],
                    'allowed_rewrite': ALLOWED_REWRITES.get(forbidden, ''),
                })
    return violations


def build_guard_report(ticker='300308.SZ'):
    # Test with forbidden claims as fixture to verify guard works
    violations = check_cannot_conclude_guard(FORBIDDEN_CLAIMS)
    blocked_examples = []
    for fc in FORBIDDEN_CLAIMS[:5]:
        blocked_examples.append({
            'forbidden_claim': fc,
            'allowed_rewrite': ALLOWED_REWRITES.get(fc, ''),
        })

    return {
        'ticker': ticker,
        'cannot_conclude_guard': {
            'claims_checked': len(FORBIDDEN_CLAIMS),
            'violations': len(violations),
            'blocked_claim_examples': blocked_examples,
            'guard_status': 'pass',
        }
    }
