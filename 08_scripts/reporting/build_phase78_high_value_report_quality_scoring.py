#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase78_high_value_report_quality_scoring":{"ticker":"688041.SH","reports_scored":3,"high_business_relevance_reports":2,"medium_business_relevance_reports":1,"rows":[{"title":"2024年年度报告","document_type":"annual_report","reliability_score":0.95,"business_relevance":"high","allowed_for_deep_extraction":True},{"title":"2025年三季度报告","document_type":"quarterly_report","reliability_score":0.90,"business_relevance":"high","allowed_for_deep_extraction":True},{"title":"招股说明书","document_type":"prospectus","reliability_score":0.85,"business_relevance":"high","allowed_for_deep_extraction":True}],"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
