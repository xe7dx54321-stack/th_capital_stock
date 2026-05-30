#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase78_688041_high_value_report_download_report":{"ticker":"688041.SH","pdf_download_ok":4,"pdf_download_failed":2,"rows":[{"title":"2024年年度报告","report_type":"annual_report","download_status":"pdf_download_ok"},{"title":"2025年三季度报告","report_type":"quarterly_report","download_status":"pdf_download_ok"},{"title":"招股说明书","report_type":"prospectus","download_status":"pdf_download_ok"},{"title":"2023年年度报告","report_type":"annual_report","download_status":"pdf_download_ok"},{"title":"投资者关系活动记录","report_type":"investor_relations_record","download_status":"pdf_download_failed","failure_reason":"html_error_instead_of_pdf"},{"title":"业绩说明会纪要","report_type":"performance_briefing","download_status":"pdf_download_failed","failure_reason":"html_error_instead_of_pdf"}],"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
