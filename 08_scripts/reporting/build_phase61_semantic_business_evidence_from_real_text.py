#!/usr/bin/env python3
"""Phase 61: Semantic Business Evidence from Real Text.
Extracts structured business evidence from validated real text spans.
Reuses Phase 60 semantic extractor logic with real text input.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_text_business_evidence_retriever import retrieve_real_text_business_evidence
from smr_real_quoted_span_validator import validate_quoted_spans
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


def extract_semantic_from_real_text(ticker='300308.SZ'):
    retrieval = retrieve_real_text_business_evidence(ticker)
    spans = retrieval['real_text_business_evidence_retrieval']['rows']
    validation = validate_quoted_spans(ticker)
    valid_map = {
        r['span_id']: r['validation_status']
        for r in validation['real_quoted_span_validation']['rows']
    }

    # Only process passed spans
    valid_spans = [s for s in spans if valid_map.get(s['span_id'], '') == 'passed']
    variables = get_business_variables()
    var_map = {v['variable']: v for v in variables}

    evidence_rows = []
    evidence_id = 0
    strengths = {'strong_direct_evidence': 0, 'medium_management_commentary': 0,
                 'weak_industry_context': 0, 'proxy_signal': 0, 'unusable': 0}

    for span in valid_spans:
        evidence_id += 1
        var_def = var_map.get(span['business_variable'], {})
        source_type = span.get('source_type', '')
        strength = EVIDENCE_STRENGTH_MAP.get(source_type, 'medium_management_commentary')

        # Downgrade: IR/QA cannot be strong_direct
        if strength == 'strong_direct_evidence' and source_type in ('investor_relations_record', 'irm_interactive_qa'):
            strength = 'medium_management_commentary'

        strengths[strength] = strengths.get(strength, 0) + 1
        is_sensitive = span['business_variable'] in SENSITIVE_VARIABLES

        evidence_rows.append({
            'evidence_id': f'real_biz_ev_{evidence_id:03d}',
            'ticker': ticker,
            'industry': 'ai_optical_module',
            'business_variable': span['business_variable'],
            'claim_type': f"{span['business_variable']}_observed",
            'source_id': span['source_id'],
            'source_type': source_type,
            'period': span['period'],
            'quoted_span': span['quoted_span'],
            'evidence_strength': strength,
            'confidence': (
                'high' if strength == 'strong_direct_evidence' else
                'medium' if strength == 'medium_management_commentary' else 'low'
            ),
            'limitation': f'管理层口径/公司材料，不能等同于量化事实。来源类型: {source_type}',
            'cannot_conclude': var_def.get('cannot_conclude_without_direct_disclosure', [])[:3],
            'requires_human_review': is_sensitive,
            'sensitive_variable': is_sensitive,
            'text_origin': 'phase50_fixture',
        })

    return {
        'ticker': ticker,
        'semantic_business_evidence_from_real_text': {
            'validated_spans_checked': len(valid_spans),
            'real_business_evidence_created': len(evidence_rows),
            'strong_direct_evidence': strengths['strong_direct_evidence'],
            'medium_management_commentary': strengths['medium_management_commentary'],
            'proxy_signal': strengths['proxy_signal'],
            'unusable': strengths['unusable'],
            'mock_evidence_used': False,
            'fixture_evidence_used': True,
            'note': 'Semantic evidence based on Phase 50 fixture text. Source types mapped to evidence strength.',
            'rows': evidence_rows,
        }
    }

def build(conn, ticker=None): return extract_semantic_from_real_text(ticker or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['semantic_business_evidence_from_real_text']
        print(f"# Semantic Business Evidence from Real Text\n- Ticker: {r['ticker']}")
        print(f"- Evidence created: {d['real_business_evidence_created']}")
        print(f"- Strong: {d['strong_direct_evidence']} | Medium: {d['medium_management_commentary']} | Proxy: {d['proxy_signal']}")
        print(f"- Mock: {d['mock_evidence_used']} | Fixture: {d['fixture_evidence_used']}")
        for ev in d['rows'][:5]:
            print(f"  - {ev['evidence_id']}: {ev['business_variable']} ({ev['evidence_strength']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
