import json,os
from datetime import datetime
def build_coverage(pe,ge):
    pr=pe.get("phase94_pricing_exploration",{}).get("results",[])
    gr=ge.get("phase94_guidance_exploration",{}).get("results",[])
    pc=[];gc=[]
    for pt,gt in zip(pr,gr):
        b=pt.get("blocked",False)
        pc.append({"ticker":pt["ticker"],"status":"blocked" if b else ("text_found" if pt["hits"]>0 else "no_text"),"hits":pt["hits"],"blocked":b})
        gc.append({"ticker":gt["ticker"],"status":"blocked" if b else ("text_found" if gt["hits"]>0 else "no_text"),"hits":gt["hits"],"blocked":b})
    return {"phase94_pricing_coverage":{"total":len(pc),"found":sum(1 for r in pc if r["status"]=="text_found"),"blocked":sum(1 for r in pc if r["blocked"]),"rows":pc},"phase94_guidance_coverage":{"total":len(gc),"found":sum(1 for r in gc if r["status"]=="text_found"),"blocked":sum(1 for r in gc if r["blocked"]),"rows":gc}}
