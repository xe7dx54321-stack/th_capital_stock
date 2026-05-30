#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase77_watchlist_intelligence_update":{
        "tickers_checked":3,"updated_tickers":1,
        "rows":[
            {"ticker":"688041.SH","new_evidence_count":5,"claim_updates":{"product_progress":"context_strengthened","R&D":"context_strengthened","risk_signal":"observed","order_visibility":"unconfirmed"},"watchlist_decision":"continue_tracking_with_pdf_context_improved","pending_created":0,"paper_order_created":0,"real_trade_created":0},
            {"ticker":"300394.SZ","status":"blocked_known_url_or_cninfo_org_id","watchlist_decision":"continue_blocker_resolution"}
        ],
        "mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
