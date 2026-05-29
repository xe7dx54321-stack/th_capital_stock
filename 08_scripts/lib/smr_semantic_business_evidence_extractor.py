#!/usr/bin/env python3
from smr_business_evidence_retriever import retrieve_business_evidence, FIXTURE_SPANS
from smr_ai_optical_business_variable_schema import get_business_variables

EVIDENCE_STRENGTH_MAP = {
    'company_announcement': 'strong_direct_evidence',
    'annual_report': 'strong_direct_evidence',
    'semiannual_report': 'strong_direct_evidence',
    'quarterly_report': 'strong_direct_evidence',
    'investor_relations_record': 'medium_management_commentary',
    'irm_interactive_qa': 'medium_management_commentary',
    'company_official_news': 'medium_management_commentary',
    'industry_public_source': 'weak_industry_context',
    'sell_side_public_excerpt': 'proxy_signal',
}

SENSITIVE_VARIABLES = {'asp_price_signal', 'customer_demand_signal'}

def extract_semantic_business_evidence(ticker='300308.SZ'):
    retrieval = retrieve_business_evidence(ticker)
    spans = retrieval['business_evidence_retrieval']['rows']
    variables = get_business_variables()
    var_map = {v['variable']: v for v in variables}

    evidence_rows = []
    evidence_id = 0
    strengths = {'strong_direct_evidence': 0, 'medium_management_commentary': 0,
                 'weak_industry_context': 0, 'proxy_signal': 0, 'unusable': 0}

    for span in spans:
        evidence_id += 1
        var_def = var_map.get(span['variable'], {})
        source_type = span.get('source_type', '')
        strength = EVIDENCE_STRENGTH_MAP.get(source_type, 'medium_management_commentary')

        # Downgrade: IR/QA cannot be strong_direct
        if strength == 'strong_direct_evidence' and source_type in ('investor_relations_record', 'irm_interactive_qa'):
            strength = 'medium_management_commentary'

        strengths[strength] = strengths.get(strength, 0) + 1
        is_sensitive = span['variable'] in SENSITIVE_VARIABLES

        evidence_rows.append({
            'evidence_id': f'biz_ev_{evidence_id:03d}',
            'ticker': ticker,
            'industry': 'ai_optical_module',
            'business_variable': span['variable'],
            'claim_type': f"{span['variable']}_observed",
            'source_id': span['source_id'],
            'source_type': source_type,
            'period': span['period'],
            'quoted_span': span['quoted_span'],
            'evidence_strength': strength,
            'confidence': 'medium' if strength == 'medium_management_commentary' else ('high' if strength == 'strong_direct_evidence' else 'low'),
            'limitation': f"管理层口径/公司材料，不能等同于量化事实。来源类型：{source_type}",
            'cannot_conclude': var_def.get('cannot_conclude_without_direct_disclosure', [])[:3],
            'requires_human_review': is_sensitive,
            'sensitive_variable': is_sensitive,
        })

    return {
        'ticker': ticker,
        'semantic_business_evidence': {
            'spans_checked': len(spans),
            'evidence_created': len(evidence_rows),
            'strong_direct_evidence': strengths['strong_direct_evidence'],
            'medium_management_commentary': strengths['medium_management_commentary'],
            'proxy_signal': strengths['proxy_signal'],
            'unusable': strengths['unusable'],
            'note': 'Fixture-based evidence. Source types mapped to evidence strength. Sensitive variables flagged.',
            'rows': evidence_rows,
        }
    }
