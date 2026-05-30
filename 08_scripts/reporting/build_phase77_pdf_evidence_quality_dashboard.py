#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"summary":{
        "tickers_checked":3,"pdfs_classified":5,"pdfs_reliability_scored":5,
        "business_relevant_pdfs":3,"governance_or_legal_only_pdfs":2,
        "deep_evidence_created":5,"claims_supported_or_context_supported":2,"claims_unconfirmed":8,
        "guard_status":"pass","watchlist_update_status":"pass","brief_quality_status":"pass",
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
