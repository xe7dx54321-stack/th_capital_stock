#!/usr/bin/env python3
import argparse,json,sys
def build():
 tickers=[{"ticker":"300308.SZ","research_status":"full_evidence_backed_tracking","cninfo":"full_chain","fallback":"optional","key_supported_claims":["800G_signal_supported"],"key_unconfirmed_claims":["asp_trend_unconfirmed"]},{"ticker":"688041.SH","research_status":"cninfo_pdf_blocked_sse_hygon_html_parsing","cninfo":"metadata_ok_pdf_blocked","fallback":"sse_html_parse_and_hygon_ir_parse","blocker":"html_parsing_network_execution_pending","key_supported_claims":[],"key_unconfirmed_claims":[]},{"ticker":"300394.SZ","research_status":"cninfo_blocked_irm_html_qa_parsing","cninfo":"identity_blocked","fallback":"irm_html_qa_parse","blocker":"irm_html_qa_extraction_network_execution_pending","key_supported_claims":[],"key_unconfirmed_claims":[]}]
 return{"phase74_research_packet":{"tickers":tickers,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:
  for t in r["phase74_research_packet"]["tickers"]:
   print("## "+t["ticker"]+": "+t["research_status"])
   if t.get("blocker"):print("- Blocker: "+t["blocker"])
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
