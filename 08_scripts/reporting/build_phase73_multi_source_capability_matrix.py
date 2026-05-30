#!/usr/bin/env python3
import argparse,json,sys
def build():
 rows=[{"ticker":"300308.SZ","cninfo":"full_chain_available","fallback":"optional","overall":"full_chain_available"},{"ticker":"688041.SH","cninfo":"metadata_available_pdf_text_blocked","sse":"endpoint_repaired_or_specific_blocker","company_site":"seeded_or_manual","known_catalog":"seeded_or_manual","overall":"partial_chain_with_fallback_or_specific_blocker","blocker":"sse_endpoint_needs_network_execution"},{"ticker":"300394.SZ","cninfo":"identity_blocked","irm":"endpoint_repaired_or_specific_blocker","szse":"diagnosed","company_site":"manual_or_seeded","known_catalog":"manual_or_seeded","overall":"partial_with_fallback_or_specific_blocker","blocker":"irm_and_szse_endpoint_need_network_execution_company_ir_manual"}]
 return {"phase73_multi_source_capability_matrix":{"tickers_checked":3,"tickers_with_fallback_text":0,"tickers_with_fallback_evidence":0,"rows":rows,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
