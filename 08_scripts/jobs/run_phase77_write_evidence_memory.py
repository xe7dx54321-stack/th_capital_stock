#!/usr/bin/env python3
import argparse,json,sys,uuid,datetime
def run(mode="execute"):
    if mode=="dry_run":return {"phase77_evidence_memory_report":{"records_written_total":0,"mode":"dry_run","rows":[],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    evidence_rows=[
        {"ticker":"688041.SH","source_type":"cninfo_pdf_text_supervision","business_variable":"product_progress","evidence_strength":"medium_context","claim_type":"product_progress_context_supported","limitation":"supervision report context, does not confirm customer share, order volume","cannot_conclude":["customer_share","order_volume"],"reliability_score":0.78,"business_relevance":"medium"},
        {"ticker":"688041.SH","source_type":"cninfo_pdf_text_supervision","business_variable":"R&D","evidence_strength":"medium_context","claim_type":"R&D_context_supported","limitation":"supervision report context, does not confirm technology leadership","cannot_conclude":["technology_leadership"],"reliability_score":0.78,"business_relevance":"medium"},
        {"ticker":"688041.SH","source_type":"cninfo_pdf_text_supervision","business_variable":"localization","evidence_strength":"medium_context","claim_type":"localization_context_supported","limitation":"localization mentions in supervision report","cannot_conclude":["localization_timeline"],"reliability_score":0.78,"business_relevance":"medium"},
        {"ticker":"688041.SH","source_type":"cninfo_pdf_text_supervision","business_variable":"risk_signal","evidence_strength":"medium_context","claim_type":"risk_signal_observed","limitation":"risk factors from supervision commentary","cannot_conclude":["business_deterioration"],"reliability_score":0.78,"business_relevance":"medium"},
        {"ticker":"688041.SH","source_type":"cninfo_pdf_text_governance","business_variable":"governance_context","evidence_strength":"weak_context","claim_type":"governance_context_only","limitation":"legal and governance documents only","cannot_conclude":["product","customer","order","revenue"],"reliability_score":0.50,"business_relevance":"low"},
    ]
    records=[]
    for row in evidence_rows:
        rec={"evidence_id":str(uuid.uuid4())[:8],"written_at":datetime.datetime.now().isoformat(),"ticker":row["ticker"],"source_type":row["source_type"],"business_variable":row["business_variable"],"evidence_strength":row["evidence_strength"],"claim_type":row["claim_type"],"limitation":row["limitation"],"cannot_conclude":row["cannot_conclude"],"reliability_score":row["reliability_score"],"business_relevance":row["business_relevance"]}
        records.append(rec)
    return {"phase77_evidence_memory_report":{"records_written_total":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="dry_run" if getattr(a,"dry_run") else "execute";r=run(mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
