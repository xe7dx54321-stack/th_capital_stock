#!/usr/bin/env python3
"""Phase 62: Chinese Business Text Chunker.
Splits normalized Chinese text into business-relevant chunks for evidence retrieval.
"""
from __future__ import annotations
import re, hashlib
from pathlib import Path
from typing import Any
from smr_chinese_text_normalizer import normalize_chinese_texts

CHUNK_TYPES = ['qa_pair', 'business_review', 'product_section',
               'financial_section', 'risk_section', 'announcement_body', 'unknown']


def _compute_chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def _classify_chunk_type(text: str) -> str:
    if '问题' in text and ('答' in text or '回复' in text):
        return 'qa_pair'
    if any(kw in text for kw in ['800G', '1.6T', '光模块', '产品', '高速']):
        return 'product_section'
    if any(kw in text for kw in ['收入', '利润', '毛利率', '营收', '业绩']):
        return 'financial_section'
    if any(kw in text for kw in ['风险', '不确定', '竞争']):
        return 'risk_section'
    if any(kw in text for kw in ['董事会', '公告', '披露']):
        return 'announcement_body'
    if any(kw in text for kw in ['管理层', '经营', '业务', '市场']):
        return 'business_review'
    return 'unknown'


def _chunk_qa_text(text: str, source_id: str) -> list[dict]:
    """Split Q&A text into individual Q&A pairs."""
    chunks = []
    # Split by Q&A patterns
    qa_blocks = re.split(r'(?=问题[一二三四五六七八九十\d]+[：:、])', text)
    for i, block in enumerate(qa_blocks):
        block = block.strip()
        if len(block) < 20:
            continue
        chunks.append({
            'chunk_id': f'chunk_{source_id}_qa_{i+1:03d}',
            'source_id': source_id,
            'chunk_type': 'qa_pair',
            'chunk_text_length': len(block),
            'chunk_hash': _compute_chunk_hash(block),
            'chunk_text_preview': block[:200],
            'allowed_usage': 'real_business_evidence_retrieval',
        })
    return chunks


def _chunk_announcement(text: str, source_id: str) -> list[dict]:
    """Split announcement into sections."""
    chunks = []
    # Split by section headers
    sections = re.split(r'(?=[一二三四五六七八九十\d]+[、.．]\s*[^\n]{2,})', text)
    for i, section in enumerate(sections):
        section = section.strip()
        if len(section) < 20:
            continue
        ct = _classify_chunk_type(section)
        chunks.append({
            'chunk_id': f'chunk_{source_id}_ann_{i+1:03d}',
            'source_id': source_id,
            'chunk_type': ct,
            'chunk_text_length': len(section),
            'chunk_hash': _compute_chunk_hash(section),
            'chunk_text_preview': section[:200],
            'allowed_usage': 'real_business_evidence_retrieval',
        })
    return chunks


def chunk_chinese_business_texts(ticker: str = '300308.SZ') -> dict:
    norm_result = normalize_chinese_texts(ticker)
    norm_rows = [r for r in norm_result['chinese_text_normalization']['rows']
                 if r['status'] == 'normalized']

    all_chunks = []
    type_counts = {}

    for row in norm_rows:
        text = row.get('normalized_text_preview', '')
        if not text:
            text = row.get('text_preview', '')
        sid = row['source_id']

        if row.get('qa_structure_detected'):
            chunks = _chunk_qa_text(text, sid)
        elif any(kw in text for kw in ['公告', '董事会']):
            chunks = _chunk_announcement(text, sid)
        else:
            ct = _classify_chunk_type(text)
            chunks = [{
                'chunk_id': f'chunk_{sid}_001',
                'source_id': sid,
                'chunk_type': ct,
                'chunk_text_length': len(text),
                'chunk_hash': _compute_chunk_hash(text),
                'chunk_text_preview': text[:200],
                'allowed_usage': 'real_business_evidence_retrieval',
            }]

        for c in chunks:
            type_counts[c['chunk_type']] = type_counts.get(c['chunk_type'], 0) + 1
        all_chunks.extend(chunks)

    return {
        'ticker': ticker,
        'chinese_business_text_chunks': {
            'texts_processed': len(norm_rows),
            'chunks_created': len(all_chunks),
            'chunk_types': type_counts,
            'note': 'Chunks derived from normalized Chinese business text. Q&A pairs preserved.',
            'rows': all_chunks,
        }
    }
