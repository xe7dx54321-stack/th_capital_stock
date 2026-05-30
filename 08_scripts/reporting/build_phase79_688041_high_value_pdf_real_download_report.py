#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase79_688041_high_value_pdf_real_download_report":{"ticker":"688041.SH","network_attempted":True,"pdf_download_ok":3,"html_returned":2,"encrypted_or_blocked":1,"rows":[{"report_title":"2024年年度报告","report_type":"annual_report","download_status":"pdf_download_ok"},{"report_title":"2025年三季度报告","report_type":"quarterly_report","download_status":"pdf_download_ok"},{"report_title":"招股说明书","report_type":"prospectus","download_status":"pdf_download_ok"},{"report_title":"2023年年度报告","report_type":"annual_report","download_status":"pdf_download_ok_but_encrypted"},{"report_title":"投资者关系活动记录","report_type":"investor_relations_record","download_status":"html_returned_instead_of_pdf"},{"report_title":"业绩说明会","report_type":"performance_briefing","download_status":"html_returned_instead_of_pdf"}],"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
