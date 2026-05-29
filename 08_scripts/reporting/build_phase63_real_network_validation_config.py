#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_network_validation_config import build_validation_config_report
def build(c,t=None): return build_validation_config_report()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None)
    if a.markdown:
        d=r['network_validation']
        print(f"# Validation Config\n- Timeout: {d['timeout']}s | Max sources: {d['max_sources']}")
        print(f"- Save raw: {d['save_raw']} | OCR: {d['ocr_allowed']} | PDF: {d['pdf_extraction']}")
        print(f"- Mock fallback: {d['mock_fallback']} | Fixture fallback: {d['fixture_fallback']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
