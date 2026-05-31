import json,os
from datetime import datetime
def run_guard(ev):
    recs=ev.get("phase94_evidence",{}).get("records",[])
    gr=[];v=0
    for r in recs:
        g={"ticker":r["ticker"],"status":"pass","violations":[]}
        for it in r.get("pricing_ev",[])+r.get("guidance_ev",[]):
            for fb in ["buy","sell","short","long","target_price","position","allocation"]:
                if fb in it.get("claim","").lower():g["violations"].append(f"trade:{fb}");v+=1
        if g["violations"]:g["status"]="violation"
        gr.append(g)
    return {"phase94_guard":{"generated_at":datetime.now().isoformat(),"overall":"pass" if v==0 else "violations","violations":v,"results":gr,"mock_used":False,"fixture_used":False}}
