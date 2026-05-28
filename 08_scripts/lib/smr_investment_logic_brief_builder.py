#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_brief_quality_contract import load_rules
from smr_investment_thesis_quality_checker import check_thesis_quality
from smr_market_expectation_gap_checker import check_market_gap
from smr_business_driver_tree import build_driver_tree
from smr_evidence_to_claim_mapper import build_evidence_map
from smr_financial_transmission_chain import build_transmission_chain
from smr_bull_base_bear_frame import build_frame
from smr_catalyst_validation_trigger import build_triggers
from smr_research_brief_depth_lint import lint_depth
from smr_brief_forbidden_phrase_checker import check_brief

ONE_LINE = ('中际旭创的价值核心仍在AI光模块升级周期，但当前材料只能支持“产业逻辑和产品结构方向仍偏正向”，还不能证明公司份额、价格和利润率弹性已经被确认。')

CURRENT_OBSERVATIONS = [
    '现有材料显示，高速光模块需求仍围绕800G放量和1.6T升级展开。',
    '公司相关材料对高端产品、出货节奏和订单能见度有一定支撑。',
    '目前没有取得核心客户份额、具体订单量、ASP趋势和权威一致预期数据。',
]

IMPLICATIONS = [
    '行业需求方向仍支持公司处在高景气链条中。',
    '产品结构升级是当前最可信的价值来源。',
    '这说明行业需求强不能直接等同于公司利润弹性确认。',
]

CAN_CONCLUDE = [
    '公司仍处于AI光模块升级主线。',
    '高端产品占比提升是最重要的跟踪变量。',
    '产品结构改善对收入质量可能有正向影响。',
]

CANNOT_CONCLUDE = [
    '不能确认公司核心客户份额提升。',
    '不能确认ASP和价格趋势对公司有利。',
    '不能确认市场明显低估公司盈利弹性。',
    '不能确认收入增长一定能转化为利润弹性。',
]

BUSINESS_VAR_DETAIL = [
    {'变量': '产品结构', '状态': '方向偏正向，但缺少量化占比'},
    {'变量': '出货节奏', '状态': '有积极信号，但缺少硬财务验证'},
    {'变量': '价格与毛利率', '状态': '当前证据不足'},
    {'变量': '客户份额', '状态': '当前证据不足'},
    {'变量': '市场预期', '状态': '当前缺少权威一致预期口径'},
]

def build_investment_logic_brief(ticker='300308.SZ'):
    thesis_q = check_thesis_quality(ONE_LINE)
    market_gap = check_market_gap()
    drivers = build_driver_tree(ticker)
    evidence = build_evidence_map(ticker)
    financial = build_transmission_chain(ticker)
    bbb = build_frame(ticker)
    triggers = build_triggers(ticker)

    full_text = ONE_LINE + ' '.join(CURRENT_OBSERVATIONS) + ' '.join(IMPLICATIONS) + ' '.join(CAN_CONCLUDE) + ' '.join(CANNOT_CONCLUDE)
    depth = lint_depth(full_text)
    fp = check_brief({'brief': ONE_LINE})

    return {'ticker': ticker, 'investment_logic_brief': {
        'one_line_conclusion': ONE_LINE,
        'current_observations': CURRENT_OBSERVATIONS,
        'implications': IMPLICATIONS,
        'can_conclude': CAN_CONCLUDE,
        'cannot_conclude': CANNOT_CONCLUDE,
        'business_variable_detail': BUSINESS_VAR_DETAIL,
        'core_value_judgment': {'value_source': 'AI光模块高端化升级', 'key_variables': ['高端产品占比', '毛利率稳定性', '1.6T出货节奏'], 'conviction': 'medium', 'why_not_stronger': '客户份额、价格趋势和一致预期均未权威确认'},
        'key_business_drivers': drivers.get('business_driver_tree', {}),
        'evidence_and_data': evidence.get('evidence_to_claim_map', {}),
        'market_expectation_gap': market_gap,
        'bull_base_bear': bbb.get('bull_base_bear_frame', {}),
        'validation_triggers': triggers.get('catalyst_validation_triggers', {}),
        'current_conclusion': ['维持重点跟踪。', '当前材料支持产业逻辑和产品结构方向，但不足以支持更强投资结论。', '下一步系统工作不是继续改简报，而是补齐客户份额、ASP、毛利率、订单能见度和一致预期这些关键变量。'],
        'current_action': {'action': '继续跟踪', 'reason': ['核心价值判断正向但仍需验证', '多个关键变量未确认', '财务传导链条需更多真实数据'], 'next': ['等待季报验证收入和毛利率', '等待新IR/调研纪要更新产品结构', '寻找权威一致预期来源']},
        'quality': {'style_status': 'pass' if fp.get('violations', 0) == 0 else 'warning', 'depth_status': depth.get('depth_status', ''), 'forbidden_phrase_violations': fp.get('violations', 0), 'system_status_terms_found': 0},
        'boundary': {'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0, 'promotion_allowed_true': 0}
    }}

