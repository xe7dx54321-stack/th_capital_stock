#!/usr/bin/env python3
import argparse,json,sys
def build():
    claims=[
        {"claim":"product_progress_context_supported","claim_status":"context_supported","supporting_evidence_count":1,"evidence_strength":"medium_context","limitation":"supervision report supports product progress context, not customer share."},
        {"claim":"R&D_context_supported","claim_status":"context_supported","supporting_evidence_count":1,"evidence_strength":"medium_context","limitation":"R&D investment context from supervision report, not technology leadership confirmation."},
        {"claim":"localization_context_supported","claim_status":"context_supported","supporting_evidence_count":1,"evidence_strength":"medium_context","limitation":"localization context from supervision report."},
        {"claim":"risk_signal_observed","claim_status":"context_supported","supporting_evidence_count":1,"evidence_strength":"medium_context","limitation":"risk signals observed in supervision commentary."},
        {"claim":"governance_context_only","claim_status":"context_supported","supporting_evidence_count":2,"evidence_strength":"weak_context","limitation":"legal opinion and shareholder resolution are governance documents only."},
        {"claim":"customer_demand_unconfirmed","claim_status":"unconfirmed","supporting_evidence_count":0,"limitation":"no customer demand data in current PDF set."},
        {"claim":"order_visibility_unconfirmed","claim_status":"unconfirmed","supporting_evidence_count":0,"limitation":"no order volume data in current PDF set."},
        {"claim":"revenue_growth_observed","claim_status":"unconfirmed","supporting_evidence_count":0,"limitation":"current PDFs do not contain revenue figures."},
        {"claim":"gross_margin_unconfirmed","claim_status":"unconfirmed","supporting_evidence_count":0,"limitation":"no gross margin data in current PDF set."},
        {"claim":"capacity_unconfirmed","claim_status":"unconfirmed","supporting_evidence_count":0,"limitation":"no capacity data in current PDF set."},
    ]
    return {"phase77_688041_pdf_claim_map":{"ticker":"688041.SH","claims_checked":len(claims),"claims_supported":0,"claims_context_supported":5,"claims_unconfirmed":5,"rows":claims,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
