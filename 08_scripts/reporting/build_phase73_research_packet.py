#!/usr/bin/env python3
import argparse,json,sys
def build():
 tickers=[{"ticker":"300308.SZ","research_status":"full_evidence_backed_tracking","cninfo":"full_chain","fallback":"optional","key_supported_claims":["800G_signal_supported","1_6T_signal_supported"],"key_unconfirmed_claims":["asp_trend_unconfirmed","customer_share_unconfirmed"]},{"ticker":"688041.SH","research_status":"cninfo_metadata_pdf_blocked_sse_endpoint_repair_attempted","cninfo":"metadata_ok_pdf_blocked","fallback":"sse_page_curated_endpoint_repair","blocker":"sse_endpoint_needs_network_execution","key_supported_claims":[],"key_unconfirmed_claims":[]},{"ticker":"300394.SZ","research_status":"cninfo_blocked_irm_szse_endpoint_repair_attempted","cninfo":"identity_blocked","fallback":"irm_szse_company_ir_seeded","blocker":"irm_endpoint_repair_and_szse_diagnostics_and_company_ir_url_need_network_execution","key_supported_claims":[],"key_unconfirmed_claims":[]}]
 return {"phase73_research_packet":{"tickers":tickers,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:
  for t in r["phase73_research_packet"]["tickers"]:
   print("## " + t["ticker"] + ": " + t["research_status"])
   if t.get("blocker"):print("- Blocker: " + t["blocker"])
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
