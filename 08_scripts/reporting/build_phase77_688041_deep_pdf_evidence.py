#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase77_pdf_document_type_classifier import classify_pdfs
from smr_phase77_pdf_business_relevance import score_business_relevance
from smr_phase77_deep_pdf_evidence_extractor import extract_deep_evidence

PHASE76_PDFS = [
    {"title": u"北京市中伦律师事务所关于海光信息技术股份有限公司2025年年度股东会的法律意见书", "text_preview": ""},
    {"title": u"海光信息技术股份有限公司2025年年度股东会决议公告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司2025年度持续督导跟踪报告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司2025年度持续督导工作现场检查报告", "text_preview": ""},
    {"title": u"中信证券股份有限公司关于海光信息技术股份有限公司持续督导保荐总结报告书", "text_preview": ""},
]

def build():
    classified = classify_pdfs(PHASE76_PDFS)
    doc_rows = classified["phase77_688041_pdf_document_type"]["rows"]
    rel = score_business_relevance(doc_rows)
    rel_rows = rel["phase77_688041_business_relevance"]["rows"]
    # merge reliability scores (simplified: use doc_type based scores)
    for i, rr in enumerate(rel_rows):
        if i < len(doc_rows):
            dt = doc_rows[i].get("document_type","unknown")
            scores = {"legal_opinion":0.55,"shareholder_meeting_resolution":0.50,"supervision_report":0.78}
            rr["reliability_score"] = scores.get(dt, 0.20)
    return extract_deep_evidence(rel_rows)

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
