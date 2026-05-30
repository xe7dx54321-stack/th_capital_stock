#!/usr/bin/env python3
import argparse,json,sys
def build():
 sb=[{"ticker":"688041.SH","source":"sse","stage":"endpoint_repair","blocker":"sse_network_execution_pending"},{"ticker":"300394.SZ","source":"irm","stage":"endpoint_repair","blocker":"irm_network_execution_pending"},{"ticker":"300394.SZ","source":"szse","stage":"endpoint_diagnostics","blocker":"szse_http_500"},{"ticker":"300394.SZ","source":"company_ir","stage":"url_filling","blocker":"manual_fill_required_after_attempt"}]
 return {"phase73_fallback_evidence_gain":{"phase72":{"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0},"phase73":{"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0},"fallback_evidence_gain_delta":0,"note":"gain_depends_on_repaired_endpoints_network_execution","source_blockers":sb,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
