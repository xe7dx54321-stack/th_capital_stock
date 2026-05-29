#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_real_disclosure_text_quality_classifier import build_quality_report
def build(t="300308.SZ"):
    return build_quality_report(t,[],skip=True)
def _md(r):
    q=r.get("real_disclosure_text_quality",r)
    lines=["# Real Disclosure Text Quality",""]
    lines.append("Checked: "+str(q.get("texts_checked",0)))
    lines.append("Usable: "+str(q.get("usable_for_business_evidence",0)))
    lines.append("Warnings: "+str(q.get("usable_with_warnings",0)))
    lines.append("Meta-only: "+str(q.get("metadata_only_not_evidence",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
