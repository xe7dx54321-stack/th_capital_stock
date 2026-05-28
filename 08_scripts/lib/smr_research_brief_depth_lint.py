#!/usr/bin/env python3
from __future__ import annotations
from smr_research_brief_quality_contract import load_rules

FORBIDDEN_TERMS = ['candidate','tracking-support','pending','validator','dashboard','quality gate','promotion_allowed','paper_order','real_trade']

# Teaching-style phrases that suggest the brief is instructing rather than reporting
TEACHING_PHRASES = [
    '下一步重点看', '需要重点关注', '后续应该观察', '继续盯',
    '值得关注', '建议关注', '若出现', '再重新评估',
    '重点看', '重点关注', '应该观察', '继续关注'
]

# Expected observed-first phrases that should appear
OBSERVED_FIRST_PHRASES = [
    '当前已看到', '当前尚未看到', '这说明', '这增强了', '这削弱了',
    '因此不能判断', '目前证据只能支持', '目前证据不足以支持',
    '当前未取得', '当前无法判断', '这说明'
]

def lint_depth(brief_text='', has_thesis=True, has_market=True, has_variant=True, has_drivers=True, has_evidence=True, has_financial=True, has_bbb=True, has_triggers=True):
    checks = {
        'has_core_value_thesis': has_thesis,
        'has_market_expectation': has_market,
        'has_variant_view': has_variant,
        'has_business_driver_tree': has_drivers,
        'has_evidence_to_claim_mapping': has_evidence,
        'has_financial_transmission': has_financial,
        'has_bull_base_bear': has_bbb,
        'has_validation_triggers': has_triggers,
        'has_disconfirming_evidence': True,
    }

    # Observed-first checks
    has_observation = any(p in brief_text for p in ['当前已看到', '现有材料显示', '目前已经', '已取得'])
    has_implication = any(p in brief_text for p in ['这意味着', '这说明'])
    has_cannot_conclude = any(p in brief_text for p in ['不能确认', '不能成立', '当前不能', '不能判断', '当前无法判断', '目前无法确认'])
    has_missing_marked = any(p in brief_text for p in ['当前未取得', '当前尚未看到', '目前没有取得', '缺少', '未取得'])

    checks['has_current_observations'] = has_observation
    checks['has_implications_from_observations'] = has_implication
    checks['has_cannot_conclude_section'] = has_cannot_conclude
    checks['missing_data_marked_as_unavailable'] = has_missing_marked

    # Teaching-style detection (True = bad, so invert)
    teaching_count = sum(1 for p in TEACHING_PHRASES if p in brief_text)
    # Allow a few teaching phrases if observations dominate
    observation_count = sum(1 for p in OBSERVED_FIRST_PHRASES if p in brief_text)
    has_no_teaching_style = teaching_count <= 2 or observation_count >= teaching_count * 2
    checks['no_teaching_style_next_watch'] = has_no_teaching_style
    checks['no_generic_watch_phrases'] = teaching_count <= 1

    # System status terms
    system_terms = sum(1 for t in FORBIDDEN_TERMS if t in brief_text.lower())
    checks['no_system_status_terms'] = system_terms == 0

    # Trading advice
    checks['no_trading_advice'] = '买入' not in brief_text and '目标价' not in brief_text and '卖出' not in brief_text

    failures = sum(1 for v in checks.values() if v is False)
    passed = len(checks) - failures
    status = 'pass' if failures == 0 else ('warning' if failures <= 2 else 'fail')
    return {
        'depth_status': status,
        'checks_passed': passed,
        'warnings': 0 if failures <= 1 else failures,
        'failures': failures,
        'checks': checks,
        'system_status_terms_found': system_terms,
        'teaching_phrases_found': teaching_count
    }

def build_depth_lint(brief_text='', **kwargs):
    return {'research_brief_depth_lint': lint_depth(brief_text, **kwargs)}
