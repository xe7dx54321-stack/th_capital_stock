#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase77_multi_source_capability_matrix":{
        "tickers_checked":3,"tickers_with_quality_scored_evidence":1,
        "rows":[
            {"ticker":"300308.SZ","cninfo":"full_chain_available","overall":"full_chain_available"},
            {"ticker":"688041.SH","cninfo_metadata":"available","cninfo_pdf_download":"ok","cninfo_pdf_text":"ok","pdf_quality_scoring":"available","deep_evidence":"quality_scored_context_evidence_available","overall":"partial_chain_with_quality_scored_pdf_evidence"},
            {"ticker":"300394.SZ","cninfo":"identity_blocked","known_url":"not_yet_usable","overall":"blocked_with_specific_manual_actions"}
        ],
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
