#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from smr_phase78_688041_high_value_report_inventory import build_high_value_inventory, REPORT_TYPE_KEYWORDS
def build():
    sample_metadata=[{"title":"海光信息2024年年度报告","pdf_url":"https://cninfo/1"},{"title":"海光信息2023年年度报告","pdf_url":"https://cninfo/2"},{"title":"海光信息2025年三季度报告","pdf_url":"https://cninfo/3"},{"title":"海光信息2025年一季报","pdf_url":"https://cninfo/4"},{"title":"海光信息招股说明书","pdf_url":"https://cninfo/5"},{"title":"海光信息投资者关系活动记录表","pdf_url":"https://cninfo/6"},{"title":"海光信息业绩说明会纪要","pdf_url":"https://cninfo/7"},{"title":"海光信息上市公告书","pdf_url":"https://cninfo/8"},{"title":"保荐机构督导报告","pdf_url":"https://cninfo/9"},{"title":"法律意见书","pdf_url":"https://cninfo/10"}]
    return build_high_value_inventory(sample_metadata)
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build();print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
