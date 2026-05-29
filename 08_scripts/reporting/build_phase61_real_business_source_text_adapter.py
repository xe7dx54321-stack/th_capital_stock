#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_business_source_text_adapter import check_real_text_availability
def build(conn,t=None): return check_real_text_availability(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_source_text_adapter']
        print(f"# Real Business Source Text Adapter\n- Ticker: {r['ticker']}")
        print(f"- Real text sources: {d['real_text_sources_available']}/{d['sources_checked']}")
        print(f"- Mock used for research: {d['mock_sources_used_for_research']}")
        print(f"- Raw saved: {d['raw_content_saved']} | OCR: {d['ocr_used']}")
        for s in d['source_rows']:
            print(f"  - {s['source_type']}: {s['status']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
