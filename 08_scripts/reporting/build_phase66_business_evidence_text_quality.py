#!/usr/bin/env python3
"""Phase 66 business evidence text quality report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_business_evidence_text_quality_scoring import score_text_quality, QUALITY_GRADES
from smr_business_keyword_hit_scanner import load_keywords

def build(t="300308.SZ"):
    r={"ticker":t,"business_evidence_text_quality":{"texts_checked":0,"high_business_signal":0,"usable_business_signal":0,"usable_with_warnings":0,"financial_context_only":0,"rejected":0,"rows":[]}}
    try:
        from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
        ex=run_expanded_extraction(t,max_pdfs=15,mode="execute")
        rows=ex.get("expanded_pdf_text_extraction",{}).get("rows",[])
        results=[]
        grades_count={g:0 for g in QUALITY_GRADES}
        for rw in rows:
            if rw.get("text_extraction_status")!="pdf_text_ok":
                continue
            text_len=rw.get("text_length",0)
            kws=rw.get("keyword_groups_hit",[])
            src_type=rw.get("source_type","other")
            # Score based on text_length + keyword density as proxy
            q=score_text_quality("business " + " ".join(kws)*5 + " disclosure "*10, src_type)
            # Adjust score with real text length
            if text_len>5000: q["score"]=min(q["score"]+10,95)
            elif text_len>2000: q["score"]=min(q["score"]+5,90)
            elif text_len<500: q["score"]=max(q["score"]-15,10)
            # Determine grade from adjusted score
            score=q["score"]
            if score>=80: grade="high_business_signal"
            elif score>=65: grade="usable_business_signal"
            elif score>=50: grade="usable_with_warnings"
            elif score>=30: grade="low_signal"
            else: grade="rejected"
            q["quality_grade"]=grade
            q["source_id"]=rw.get("source_id","")
            q["title"]=(rw.get("title","") or "")[:80]
            q["text_length"]=text_len
            q["keyword_groups_hit"]=kws
            grades_count[grade]=grades_count.get(grade,0)+1
            results.append(q)
        r["business_evidence_text_quality"]={
            "texts_checked":len(results),
            "high_business_signal":grades_count.get("high_business_signal",0),
            "usable_business_signal":grades_count.get("usable_business_signal",0),
            "usable_with_warnings":grades_count.get("usable_with_warnings",0),
            "financial_context_only":grades_count.get("financial_context_only",0),
            "low_signal":grades_count.get("low_signal",0),
            "rejected":grades_count.get("rejected",0),
            "rows":sorted(results,key=lambda x:-x["score"])
        }
        return r
    except Exception as e:
        r["business_evidence_text_quality"]["status"]="error:"+str(e)[:80]
        return r

def _md(r):
    q=r.get("business_evidence_text_quality",r)
    lines=["# Business Evidence Text Quality",""]
    lines.append("Checked: "+str(q.get("texts_checked",0)))
    lines.append("High signal: "+str(q.get("high_business_signal",0)))
    lines.append("Usable: "+str(q.get("usable_business_signal",0)))
    lines.append("Warnings: "+str(q.get("usable_with_warnings",0)))
    lines.append("Rejected: "+str(q.get("rejected",0)))
    for row in q.get("rows",[])[:5]:
        lines.append("- "+str(row.get("title",""))[:50]+" ["+str(row.get("quality_grade",""))+"]")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
