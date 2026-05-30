#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from smr_phase78_business_relevance_chinese_matcher import score_business_relevance_chinese
def build():
    sample_pdfs=[
        {"title":"海光信息2024年年度报告","text_preview":"公司2024年实现营业收入68.52亿元同比增长超过80%研发投入持续加大高端处理器国产化进程加速","document_type":"annual_report"},
        {"title":"海光信息2025年三季度报告","text_preview":"前三季度营业收入继续保持增长毛利率维持在较高水平客户对国产高端处理器需求旺盛","document_type":"quarterly_report"},
        {"title":"海光信息招股说明书","text_preview":"公司主营业务为高端处理器研发设计和销售产品包括通用处理器CPU和协处理器DCU","document_type":"prospectus"},
        {"title":"海光信息法律意见书","text_preview":"本所接受委托就海光信息股东大会相关事项出具法律意见","document_type":"legal_opinion"},
        {"title":"海光信息股东会决议","text_preview":"股东大会审议通过了关于选举董事的议案","document_type":"shareholder_meeting_resolution"},
    ]
    return score_business_relevance_chinese(sample_pdfs)
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
