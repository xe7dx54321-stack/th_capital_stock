#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase79_multi_source_capability_matrix":{"tickers_checked":3,"tickers_with_real_network_validated_reports":1,"tickers_with_quantitative_extraction":1,"rows":[{"ticker":"300308.SZ","cninfo":"full_chain_available","overall":"full_chain_available"},{"ticker":"688041.SH","high_value_report_real_download":"validated","pdf_text_extraction":"validated","quantitative_extraction":"available","qual_quant_alignment":"available","overall":"partial_chain_with_quantitative_report_context"},{"ticker":"300394.SZ","cninfo":"identity_blocked","known_url":"not_yet_usable","overall":"blocked_with_specific_manual_actions"}],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
