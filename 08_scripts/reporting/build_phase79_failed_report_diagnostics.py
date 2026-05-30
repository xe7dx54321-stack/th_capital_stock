#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase79_failed_report_diagnostics":{"failed_reports_checked":3,"rows":[{"report_title":"2023年年度报告","failure_type":"encrypted_pdf","ocr_used":False,"browser_automation_used":False,"allowed_next_action":"find_alternative_non_encrypted_pdf_or_later_report","not_allowed_action":"bypass_encryption_or_ocr"},{"report_title":"投资者关系活动记录","failure_type":"html_returned_instead_of_pdf","allowed_next_action":"parse_html_for_real_pdf_link_or_use_text_page_if_static","not_allowed_action":"treat_html_as_pdf_text"},{"report_title":"业绩说明会","failure_type":"html_returned_instead_of_pdf","allowed_next_action":"parse_html_for_real_pdf_link_or_use_text_page_if_static","not_allowed_action":"treat_html_as_pdf_text"}]}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
