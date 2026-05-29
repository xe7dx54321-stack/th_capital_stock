#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_chinese_text_normalizer import normalize_chinese_texts
def build(conn,t=None): return normalize_chinese_texts(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['chinese_text_normalization']
        print(f"# Chinese Text Normalization\n- Ticker: {r['ticker']}")
        print(f"- Checked: {d['texts_checked']} | Normalized: {d['normalized']} | Too short: {d['too_short']}")
        print(f"- QA detected: {d['qa_structure_detected']} | Disclaimers removed: {d['disclaimer_removed']}")
        for row in d['rows'][:5]:
            print(f"  - {row['source_id']}: {row['status']} ({row.get('normalized_text_length', 0)} chars)")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
