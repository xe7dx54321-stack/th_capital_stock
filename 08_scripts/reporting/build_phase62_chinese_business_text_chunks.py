#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_chinese_business_text_chunker import chunk_chinese_business_texts
def build(conn,t=None): return chunk_chinese_business_texts(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['chinese_business_text_chunks']
        print(f"# Chinese Business Text Chunks\n- Ticker: {r['ticker']}")
        print(f"- Texts: {d['texts_processed']} | Chunks: {d['chunks_created']}")
        print(f"- Types: {d['chunk_types']}")
        for row in d['rows'][:8]:
            print(f"  - {row['chunk_id']}: {row['chunk_type']} ({row['chunk_text_length']} chars)")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
