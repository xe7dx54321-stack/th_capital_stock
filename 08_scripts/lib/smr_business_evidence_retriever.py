#!/usr/bin/env python3
from smr_ai_optical_business_variable_schema import get_business_variables
from smr_business_source_inventory import build_business_source_inventory

# Fixture evidence spans based on 300308.SZ known disclosures
FIXTURE_SPANS = {
    '800G_product_signal': [
        {'span_id': 'biz_span_800g_01', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '公司800G光模块产品已实现批量交付，下游客户需求旺盛。',
         'retrieval_reason': 'keyword_800G_section_match', 'period': '2025Q2'},
        {'span_id': 'biz_span_800g_02', 'source_id': 'ann_2025_001', 'source_type': 'company_announcement',
         'quoted_span': '公司800G高速光模块产品已通过主要客户认证并进入规模交付阶段。',
         'retrieval_reason': 'keyword_800G_announcement', 'period': '2025Q1'},
        {'span_id': 'biz_span_800g_03', 'source_id': 'qa_2025_001', 'source_type': 'irm_interactive_qa',
         'quoted_span': '800G产品出货节奏正常，产能利用率持续提升。',
         'retrieval_reason': 'keyword_800G_QA_match', 'period': '2025Q2'},
    ],
    '1_6T_product_signal': [
        {'span_id': 'biz_span_16t_01', 'source_id': 'news_2025_001', 'source_type': 'company_official_news',
         'quoted_span': '公司在OFC 2025展示了1.6T OSFP-XD光模块产品，已向客户送样。',
         'retrieval_reason': 'keyword_1.6T_news', 'period': '2025Q2'},
        {'span_id': 'biz_span_16t_02', 'source_id': 'qa_2024_001', 'source_type': 'irm_interactive_qa',
         'quoted_span': '1.6T产品正在客户验证阶段，预计2025年下半年进入量产。',
         'retrieval_reason': 'keyword_1.6T_QA', 'period': '2024Q4'},
        {'span_id': 'biz_span_16t_03', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '下一代1.6T产品研发进展顺利，预计年内完成客户认证。',
         'retrieval_reason': 'keyword_next_gen', 'period': '2025Q2'},
    ],
    'high_end_product_mix': [
        {'span_id': 'biz_span_mix_01', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '公司高端产品占比持续提升，产品结构进一步优化。',
         'retrieval_reason': 'keyword_product_mix', 'period': '2025Q2'},
        {'span_id': 'biz_span_mix_02', 'source_id': 'ar_2024', 'source_type': 'annual_report',
         'quoted_span': '高速光模块产品收入占比显著提高，推动整体毛利率改善。',
         'retrieval_reason': 'keyword_high_speed_revenue', 'period': '2024Q4'},
    ],
    'shipment_delivery_signal': [
        {'span_id': 'biz_span_ship_01', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '目前出货节奏符合预期，产能能够满足下游客户需求。',
         'retrieval_reason': 'keyword_shipment', 'period': '2025Q2'},
        {'span_id': 'biz_span_ship_02', 'source_id': 'ir_2025Q1_001', 'source_type': 'investor_relations_record',
         'quoted_span': '公司排产饱满，交付能力持续增强。',
         'retrieval_reason': 'keyword_delivery', 'period': '2025Q1'},
    ],
    'customer_demand_signal': [
        {'span_id': 'biz_span_cust_01', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '海外头部客户需求持续旺盛，AI算力投资拉动光模块需求。',
         'retrieval_reason': 'keyword_customer_demand', 'period': '2025Q2'},
        {'span_id': 'biz_span_cust_02', 'source_id': 'ir_2024Q4_001', 'source_type': 'investor_relations_record',
         'quoted_span': '云厂商资本开支增长带动高速光模块需求。',
         'retrieval_reason': 'keyword_cloud_capex', 'period': '2024Q4'},
    ],
    'asp_price_signal': [
        {'span_id': 'biz_span_asp_01', 'source_id': 'ir_2024Q4_001', 'source_type': 'investor_relations_record',
         'quoted_span': '公司产品定价策略保持稳定，高端产品ASP相对较高。',
         'retrieval_reason': 'keyword_ASP_pricing', 'period': '2024Q4'},
    ],
    'order_visibility_signal': [
        {'span_id': 'biz_span_order_01', 'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record',
         'quoted_span': '在手订单充足，能见度覆盖未来数个季度。',
         'retrieval_reason': 'keyword_order_visibility', 'period': '2025Q2'},
        {'span_id': 'biz_span_order_02', 'source_id': 'ir_2025Q1_001', 'source_type': 'investor_relations_record',
         'quoted_span': '下游订单能见度较好，客户下单节奏稳定。',
         'retrieval_reason': 'keyword_order_rhythm', 'period': '2025Q1'},
    ],
}

def retrieve_business_evidence(ticker='300308.SZ'):
    inventory = build_business_source_inventory(ticker)
    sources_available = inventory['business_source_inventory']['sources_available']
    variables = get_business_variables()

    all_spans = []
    hit_variables = set()
    for var in variables:
        var_name = var['variable']
        spans = FIXTURE_SPANS.get(var_name, [])
        if spans:
            hit_variables.add(var_name)
            for s in spans:
                all_spans.append({**s, 'variable': var_name, 'final_judgment': 'not_yet_judged'})

    return {
        'ticker': ticker,
        'business_evidence_retrieval': {
            'sources_scanned': sources_available,
            'candidate_spans_found': len(all_spans),
            'variables_hit': sorted(hit_variables),
            'note': 'Fixture-based evidence spans based on known 300308.SZ disclosure patterns. Not real scraped text.',
            'raw_content_saved': False,
            'rows': all_spans,
        }
    }
