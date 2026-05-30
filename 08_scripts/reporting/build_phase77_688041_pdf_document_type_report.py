#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase77_pdf_document_type_classifier import classify_pdfs

# 5 PDFs from Phase 76 real execute
PHASE76_PDFS = [
    {"title": u"北京市中伦律师事务所关于海光信息技术股份有限公司2025年年度股东会的法律意见书", "text_preview": ""},
    {"title": u"海光信息技术股份有限公司2025年年度股东会决议公告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司2025年度持续督导跟踪报告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司2025年度持续督导工作现场检查报告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司持续督导保荐总结报告书", "text_preview": ""},
]

def build():
    return classify_pdfs(PHASE76_PDFS)

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
