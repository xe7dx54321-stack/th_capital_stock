#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH; from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_text_availability import IR_FIXTURE, ANNUAL_FIXTURE, QUARTERLY_FIXTURE, EARNINGS_FIXTURE, ANNOUNCE_FIXTURE
from smr_chunk_quality_classifier import build_chunk_quality
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

def build(conn,ticker):
    sources=get_sample_sources(ticker)
    fm=[(IR_FIXTURE,'cninfo_investor_relations'),(ANNUAL_FIXTURE,'cninfo_annual_report'),(QUARTERLY_FIXTURE,'cninfo_quarterly_report'),(EARNINGS_FIXTURE,'cninfo_earnings_preview'),(ANNOUNCE_FIXTURE,'cninfo_announcement')]
    chunks=[{'chunk_id':f'chunk_{i}','source_id':s.get('source_id'),'chunk_type':('qa_section' if i==0 else 'product_business_description' if i==1 else 'shipment_delivery_commentary' if i==2 else 'financial_section' if i==3 else 'unknown'),'content':next((t for t,st in fm if st==s.get('source_type')),''),'text_chars':len(next((t for t,st in fm if st==s.get('source_type')),'')),'ticker':ticker} for i,s in enumerate(sources) if next((t for t,st in fm if st==s.get('source_type')),'')]
    return build_chunk_quality(chunks,ticker)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true')
    p.add_argument('--markdown',action='store_true')
    args=p.parse_args()
    result=build(None,args.ticker)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
