#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase73_fallback_text_quality import classify_fallback_text
def build():
 samples=[("300394.SZ","irm","管理层回复：公司光模块业务进展顺利。"),("688041.SH","sse",""),("300394.SZ","company_ir_page","证券代码 证券简称 公告日期")]
 rows=[classify_fallback_text(t,st,tx) for t,st,tx in samples]
 usable=sum(1 for r in rows if "usable" in r.get("quality_grade",""))
 meta=sum(1 for r in rows if r.get("quality_grade")=="metadata_only")
 rej=sum(1 for r in rows if r.get("quality_grade") in ("rejected","text_too_short"))
 return {"phase73_fallback_text_quality":{"texts_checked":len(rows),"texts_usable":usable,"metadata_only":meta,"rejected":rej,"rows":rows,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
