#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_text_extraction_quality_classifier import classify_extraction_quality
def build(conn,t=None): return classify_extraction_quality(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_text_extraction_quality']
        print(f"# Text Extraction Quality\n- Ticker: {r['ticker']} | Checked: {d['texts_checked']}")
        print(f"- Usable: {d['usable_for_business_evidence']} | Warnings: {d['usable_with_warnings']}")
        print(f"- Metadata only: {d['metadata_only_not_evidence']} | Too short: {d['too_short_not_evidence']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
