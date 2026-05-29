#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_text_business_evidence_retriever import retrieve_real_text_business_evidence
def build(conn,t=None): return retrieve_real_text_business_evidence(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_text_business_evidence_retrieval']
        print(f"# Real Text Business Evidence Retrieval\n- Ticker: {r['ticker']}")
        print(f"- Sources scanned: {d['real_text_sources_scanned']}")
        print(f"- Spans found: {d['candidate_spans_found']}")
        print(f"- Variables hit: {d['variables_hit']}")
        print(f"- Mock spans used: {d['mock_spans_used']}")
        for s in d['rows'][:5]:
            print(f"  - {s['span_id']}: {s['business_variable']} ({s['source_type']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
