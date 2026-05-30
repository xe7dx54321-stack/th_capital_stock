#!/usr/bin/env python3
import argparse,json,sys
def build():
 sb=[{"ticker":"688041.SH","source":"sse_html","stage":"html_parsing_links","blocker":"sse_links_extraction_network_execution_pending"},{"ticker":"300394.SZ","source":"irm_html","stage":"html_qa_parsing","blocker":"irm_html_qa_extraction_network_execution_pending"},{"ticker":"688041.SH","source":"hygon_ir","stage":"html_text_extraction","blocker":"hygon_ir_page_network_execution_pending"}]
 return{"phase74_fallback_evidence_gain":{"phase73":{"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0},"phase74":{"fallback_texts_usable":0,"fallback_deep_evidence_created":0,"tickers_with_fallback_gain":0},"fallback_evidence_gain_delta":0,"note":"gain_awaits_html_parsing_network_execution","source_blockers":sb,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
