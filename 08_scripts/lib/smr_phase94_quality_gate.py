import json,os
from datetime import datetime
def run_gate(ev):
    recs=ev.get("phase94_evidence",{}).get("records",[])
    gr=[];s={"passed":0,"review":0,"rejected":0}
    for r in recs:
        g={"ticker":r["ticker"],"status":"passed","chks":[]}
        for it in r.get("pricing_ev",[])+r.get("guidance_ev",[]):
            c={"type":it["type"],"status":"passed","issues":[]}
            if it["conf"]=="low":c["issues"].append("low_conf")
            if it["type"]=="blocked":c["status"]="review";c["issues"].append("blocked")
            if "buy_signal" in str(it.get("cannot",[])):c["status"]="rejected";c["issues"].append("trade_violation")
            g["chks"].append(c)
        if any(c["status"]=="rejected" for c in g["chks"]):g["status"]="rejected";s["rejected"]+=1
        elif any(c["status"]=="review" for c in g["chks"]):g["status"]="review";s["review"]+=1
        else:s["passed"]+=1
        gr.append(g)
    return {"phase94_gate":{"generated_at":datetime.now().isoformat(),"summary":s,"results":gr,"mock_used":False,"fixture_used":False}}
