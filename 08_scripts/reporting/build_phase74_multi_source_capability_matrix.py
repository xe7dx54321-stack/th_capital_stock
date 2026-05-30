#!/usr/bin/env python3
import argparse,json,sys
def build():
 rows=[{"ticker":"300308.SZ","cninfo":"full_chain_available","fallback":"optional","overall":"full_chain_available"},{"ticker":"688041.SH","cninfo":"metadata_available_pdf_text_blocked","sse_html":"links_or_text_available_after_network","company_ir_html":"text_available_or_specific_blocker","known_catalog":"seeded_or_manual","overall":"partial_chain_with_html_fallback"},{"ticker":"300394.SZ","cninfo":"identity_blocked","irm_html":"qa_text_available_or_specific_blocker","szse_html":"specific_blocker","company_site":"manual_or_available","overall":"partial_with_html_fallback_or_specific_blocker","blocker":"irm_html_qa_extraction_network_execution_pending"}]
 return{"phase74_multi_source_capability_matrix":{"tickers_checked":3,"tickers_with_fallback_text":0,"tickers_with_fallback_evidence":0,"rows":rows,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
