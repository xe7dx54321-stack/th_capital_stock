#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase78_688041_existing_pdf_rescan":{
        "ticker":"688041.SH","pdfs_rescanned":5,
        "new_variable_hits":{"product_progress":1,"revenue_growth":1,"localization":1,"risk_signal":1},
        "still_unconfirmed":["customer_demand","order_visibility","capacity"],
        "legal_governance_exclusion_applied":True,
        "rows":[
            {"title":"2024年度持续督导跟踪报告","document_type":"supervision_report","matched_variables":["R&D","risk_signal","product_progress"],"business_relevance_after_repair":"medium","allowed_for_deep_extraction":True},
            {"title":"2024年度持续督导现场检查报告","document_type":"supervision_report","matched_variables":["R&D","localization"],"business_relevance_after_repair":"medium","allowed_for_deep_extraction":True},
            {"title":"保荐机构年度总结报告","document_type":"supervision_report","matched_variables":["R&D","revenue_growth"],"business_relevance_after_repair":"medium","allowed_for_deep_extraction":True},
            {"title":"法律意见书","document_type":"legal_opinion","matched_variables":[],"business_relevance_after_repair":"low","allowed_for_deep_extraction":False},
            {"title":"股东大会决议","document_type":"shareholder_meeting_resolution","matched_variables":[],"business_relevance_after_repair":"low","allowed_for_deep_extraction":False},
        ],
        "mock_used":False,"fixture_used":False
    }}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
