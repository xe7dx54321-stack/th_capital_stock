#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_html_text_quality_classifier import classify_html_text
def build():
 samples=[("300394.SZ","irm_html","管理层回复：公司光模块业务进展顺利，产能持续提升。",0),("688041.SH","sse_html","证券代码 证券简称 公告日期 公告标题 公告编号",5),("688041.SH","company_ir_page","关于公司的业务介绍，产品线包括高端处理器和加速器",0)]
 rows=[classify_html_text(t,st,tx,lc) for t,st,tx,lc in samples]
 usable=sum(1 for r in rows if "usable" in r.get("quality_grade",""))
 meta=sum(1 for r in rows if r.get("quality_grade")=="metadata_only")
 rej=sum(1 for r in rows if r.get("quality_grade") in ("rejected","text_too_short","link_only_page"))
 return{"phase74_html_text_quality":{"texts_checked":len(rows),"texts_usable":usable,"metadata_only":meta,"rejected":rej,"rows":rows}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
