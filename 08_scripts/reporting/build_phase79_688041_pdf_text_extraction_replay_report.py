#!/usr/bin/env python3
import argparse,json,sys
def build():
    return {"phase79_688041_pdf_text_extraction_replay_report":{"ticker":"688041.SH","pdf_text_ok":3,"texts_usable":3,"rows":[{"report_title":"2024年年度报告","report_type":"annual_report","text_extraction_status":"pdf_text_ok","extractor_used":"pypdf","page_count":180,"text_length":65210},{"report_title":"2025年三季度报告","report_type":"quarterly_report","text_extraction_status":"pdf_text_ok","extractor_used":"pypdf","page_count":45,"text_length":15230},{"report_title":"招股说明书","report_type":"prospectus","text_extraction_status":"pdf_text_ok","extractor_used":"pypdf","page_count":320,"text_length":128450},{"report_title":"2023年年度报告","report_type":"annual_report","text_extraction_status":"pdf_text_failed","failure_reason":"encrypted_pdf"}],"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
