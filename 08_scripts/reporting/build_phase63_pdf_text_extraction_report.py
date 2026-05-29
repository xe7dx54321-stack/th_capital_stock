#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_controlled_pdf_text_extractor import run_pdf_text_extraction
def build(conn,t=None): return run_pdf_text_extraction(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['pdf_text_extraction_report']
        print(f"# PDF Text Extraction\n- Ticker: {r['ticker']}")
        print(f"- Checked: {d['pdf_sources_checked']} | Extracted: {d['pdf_text_extracted']} | Failed: {d['pdf_text_failed']}")
        print(f"- OCR: {d['ocr_used']} | Raw PDF saved: {d['raw_pdf_saved']}")
        for row in d['rows']: print(f"  - {row['source_id']}: {row['extraction_status']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
