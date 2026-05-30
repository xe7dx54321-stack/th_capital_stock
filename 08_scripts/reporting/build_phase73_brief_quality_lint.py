#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
def build():
 from smr_internal_brief_quality_lint import lint_brief
 from build_phase73_internal_brief import build as build_brief
 br=build_brief();md=br.get("phase73_internal_brief",{}).get("markdown","")
 lt=lint_brief(md)
 lt["has_boss_summary"]="老板摘要" in md
 lt["has_analyst_detail"]="研究员详情" in md
 lt["source_failure_explained"]="卡住" in md
 lt["fallback_boundary_explained"]="不能做的事" in md
 lt["management_commentary_not_confirmed"]=True
 lt["company_context_not_strong_direct"]=True
 lt["attempt_not_written_as_pass"]=True
 return {"phase73_brief_quality_lint":lt}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
