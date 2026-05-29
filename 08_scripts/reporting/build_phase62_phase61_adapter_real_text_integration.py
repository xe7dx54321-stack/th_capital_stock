#!/usr/bin/env python3
"""Phase 62: Phase 61 Adapter Real Text Integration."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_chinese_business_text_chunker import chunk_chinese_business_texts
from smr_real_business_source_text_adapter import check_real_text_availability

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    chunks = chunk_chinese_business_texts(ticker)
    adapter = check_real_text_availability(ticker)
    cd = chunks['chinese_business_text_chunks']
    ad = adapter['real_business_source_text_adapter']

    has_real_text = cd['chunks_created'] > 0
    phase50_replaced = has_real_text

    return {'ticker': ticker, 'phase61_adapter_real_text_integration': {
        'phase50_fixture_replaced': phase50_replaced,
        'real_chinese_text_sources': cd['texts_processed'],
        'real_chinese_chunks': cd['chunks_created'],
        'chunk_types': cd['chunk_types'],
        'phase61_adapter_ready': has_real_text,
        'mock_sources_used_for_research': False,
        'fixture_text_used_for_research': not phase50_replaced,
        'metadata_only_used_as_text': False,
        'raw_content_saved': False,
        'ocr_used': False,
        'note': ('Phase 50 fixture replaced by real Chinese business text chunks.' if phase50_replaced
                 else 'Insufficient real Chinese text. Phase 50 fixture NOT used as fallback.'),
    }}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['phase61_adapter_real_text_integration']
        print(f"# Phase 61 Adapter Real Text Integration\n- Ticker: {r['ticker']}")
        print(f"- Fixture replaced: {d['phase50_fixture_replaced']}")
        print(f"- Real chunks: {d['real_chinese_chunks']} | Ready: {d['phase61_adapter_ready']}")
        print(f"- Fixture used: {d['fixture_text_used_for_research']} | Mock: {d['mock_sources_used_for_research']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
