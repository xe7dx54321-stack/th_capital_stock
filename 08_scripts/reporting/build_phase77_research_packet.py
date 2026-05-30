#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase77_research_packet":{
        "tickers_checked":3,
        "key_finding":"688041_5_pdfs_classified_3_supervision_1_legal_1_governance_deep_evidence_from_supervision_only",
        "rows":[
            {"ticker":"300308.SZ","baseline_status":"not_regressed","cninfo":"full_chain_available","evidence_count":23},
            {"ticker":"688041.SH","baseline_status":"pdf_quality_scored","pdfs_classified":5,"business_relevant":2,"governance_or_legal":3,"deep_evidence":5,"evidence_strength":"context_only"},
            {"ticker":"300394.SZ","baseline_status":"blocker_preserved","blocker":"cninfo_org_id_and_known_url"}
        ],
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
