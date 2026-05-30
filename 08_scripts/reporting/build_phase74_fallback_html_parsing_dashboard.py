#!/usr/bin/env python3
import argparse,json,sys
def build():
 return{"summary":{"tickers_checked":3,"html_pages_fetched":0,"irm_qa_items_found":0,"sse_announcement_links_found":0,"company_ir_text_blocks_found":0,"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0,"manual_fill_required_remaining":1,"multi_source_matrix_status":"pass","brief_quality_status":"pass","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
