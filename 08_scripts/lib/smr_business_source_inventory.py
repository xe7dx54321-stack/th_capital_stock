#!/usr/bin/env python3
from smr_ai_optical_business_variable_schema import get_business_variables

SOURCE_TYPES = [
    'company_announcement', 'annual_report', 'semiannual_report',
    'quarterly_report', 'investor_relations_record', 'irm_interactive_qa',
    'company_official_news', 'industry_public_source', 'sell_side_public_excerpt',
]

# Mock source inventory for 300308.SZ - represents known IR/interaction records
MOCK_SOURCES = [
    {'source_id': 'ir_2025Q2_001', 'source_type': 'investor_relations_record', 'period': '2025Q2', 'title': '投资者关系活动记录表（2025年5月）', 'text_available': True},
    {'source_id': 'ir_2024Q4_001', 'source_type': 'investor_relations_record', 'period': '2024Q4', 'title': '投资者关系活动记录表（2024年11月）', 'text_available': True},
    {'source_id': 'ir_2024Q3_001', 'source_type': 'investor_relations_record', 'period': '2024Q3', 'title': '投资者关系活动记录表（2024年9月）', 'text_available': True},
    {'source_id': 'ar_2024', 'source_type': 'annual_report', 'period': '2024Q4', 'title': '2024年年度报告', 'text_available': True},
    {'source_id': 'ar_2023', 'source_type': 'annual_report', 'period': '2023Q4', 'title': '2023年年度报告', 'text_available': True},
    {'source_id': 'sr_2025H1', 'source_type': 'semiannual_report', 'period': '2025Q2', 'title': '2025年半年度报告', 'text_available': True},
    {'source_id': 'qr_2025Q1', 'source_type': 'quarterly_report', 'period': '2025Q1', 'title': '2025年第一季度报告', 'text_available': True},
    {'source_id': 'ann_2025_001', 'source_type': 'company_announcement', 'period': '2025Q1', 'title': '关于800G光模块产品进展公告', 'text_available': True},
    {'source_id': 'news_2025_001', 'source_type': 'company_official_news', 'period': '2025Q2', 'title': '公司参加OFC 2025展示1.6T产品', 'text_available': True},
    {'source_id': 'qa_2025_001', 'source_type': 'irm_interactive_qa', 'period': '2025Q2', 'title': '互动易：关于800G出货节奏', 'text_available': True},
    {'source_id': 'qa_2024_001', 'source_type': 'irm_interactive_qa', 'period': '2024Q4', 'title': '互动易：关于1.6T产品验证进展', 'text_available': True},
    {'source_id': 'ir_2025Q1_001', 'source_type': 'investor_relations_record', 'period': '2025Q1', 'title': '投资者关系活动记录表（2025年3月）', 'text_available': True},
]

def build_business_source_inventory(ticker='300308.SZ'):
    sources = MOCK_SOURCES
    available = [s for s in sources if s['text_available']]
    type_counts = {}
    for s in available:
        t = s['source_type']
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        'ticker': ticker,
        'business_source_inventory': {
            'sources_checked': len(sources),
            'sources_available': len(available),
            'source_types': type_counts,
            'raw_content_saved': False,
            'ocr_used': False,
            'note': 'Mock source inventory based on known 300308.SZ disclosure patterns. Not real scraped data.',
            'rows': [{
                'source_id': s['source_id'], 'source_type': s['source_type'],
                'period': s['period'], 'title': s['title'],
                'text_available': s['text_available'],
                'allowed_usage': 'business_evidence_extraction' if s['text_available'] else 'metadata_only'
            } for s in sources],
        }
    }
