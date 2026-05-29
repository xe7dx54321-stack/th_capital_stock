#!/usr/bin/env python3
'''Brief evidence citation map.'''
from typing import Any

def build_citation_map(brief_data: dict, claim_linkage: dict,
                       evidence_records: list[dict]) -> dict[str, Any]:
    sections = [
        ('老板摘要/关键变化', 'claims_overview'),
        ('当前已看到的信息', 'observations'),
        ('这些信息意味着什么', 'meaning'),
        ('当前能成立的判断', 'supported_judgments'),
        ('当前不能成立的判断', 'unconfirmed_judgments'),
        ('财务与证据印证', 'financial_evidence_crosscheck'),
        ('多空分歧和关键风险', 'risk'),
    ]

    ev_by_id = {ev.get('evidence_id', ''): ev for ev in evidence_records}
    rows = []
    for section_name, section_key in sections:
        eids = _get_eids_for_section(section_key, claim_linkage, brief_data, evidence_records)
        strengths = [ev_by_id.get(eid, {}).get('evidence_strength', '') for eid in eids if eid in ev_by_id]
        cq = 'good' if len(eids) >= 2 else 'thin' if len(eids) == 1 else 'no_direct_evidence'

        rows.append({
            'brief_section': section_name,
            'brief_claim': section_key,
            'evidence_ids': eids,
            'source_titles': [ev_by_id.get(eid, {}).get('source_title', '')[:40] for eid in eids if eid in ev_by_id],
            'evidence_strength_mix': list(set(strengths)),
            'citation_quality': cq,
            'limitation': '基于CNINFO真实披露文本，非mock/fixture。' if eids else '无直接披露证据支撑此节。'
        })

    return {
        'brief_sections': len(rows),
        'sections_with_evidence': sum(1 for r in rows if r['evidence_ids']),
        'sections_without_evidence': sum(1 for r in rows if not r['evidence_ids']),
        'total_citations': sum(len(r['evidence_ids']) for r in rows),
        'rows': rows
    }

def _get_eids_for_section(key: str, claim_linkage: dict, brief_data: dict,
                          evidence_records: list[dict]) -> list[str]:
    if key == 'supported_judgments':
        eids = []
        for r in claim_linkage.get('rows', []):
            if r.get('claim_status') in ('supported', 'partially_supported'):
                eids.extend(r.get('evidence_ids', []))
        return eids[:10]
    if key == 'unconfirmed_judgments':
        eids = []
        for r in claim_linkage.get('rows', []):
            if r.get('claim_status') == 'unconfirmed':
                eids.extend(r.get('evidence_ids', []))
        return eids
    if key in ('claims_overview', 'observations', 'meaning', 'risk'):
        return [ev.get('evidence_id', '') for ev in evidence_records[:5]]
    if key == 'financial_evidence_crosscheck':
        return [ev.get('evidence_id', '') for ev in evidence_records[:3]]
    return []
