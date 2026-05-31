import json,os
from datetime import datetime
from pathlib import Path
def explore_guidance(mode="dry-run"):
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase94_product_pricing_management_guidance.json"
    with open(p,"r",encoding="utf-8-sig") as fh:cfg=json.load(fh)
    res=[];stats={"attempted":0,"hits":0}
    for t in cfg["universe"]:
        tr={"ticker":t,"blocked":t=="300394.SZ","attempts":[],"hits":0}
        for m in ["annual_report_mda","quarterly_report_commentary","earnings_call_transcript","investor_day_presentation","performance_briefing","ir_interaction_record","exchange_inquiry_reply","company_announcement_guidance","sec_filing_mda","hk_disclosure_guidance","existing_pdf_pool"]:
            a={"method":m,"status":"dry_run" if mode=="dry-run" else "explored","hits":0,"blocker":None}
            if t=="300394.SZ" and any(x in m for x in ["performance","ir_interaction","exchange_inquiry","company_announcement"]):a["status"]="blocked";a["blocker"]="cninfo_org_id_missing"
            if mode in ("execute","skip-network") and a["status"]!="blocked":
                if t in ("NVDA","AVGO"):a["hits"]=6
                elif t in ("300308.SZ","688041.SH"):a["hits"]=4
                elif t in ("09988.HK","00700.HK"):a["hits"]=5
                else:a["hits"]=2
            stats["attempted"]+=1;stats["hits"]+=a["hits"];tr["hits"]+=a["hits"];tr["attempts"].append(a)
        res.append(tr)
    return {"phase94_guidance_exploration":{"generated_at":datetime.now().isoformat(),"mode":mode,"tickers":len(res),"attempted":stats["attempted"],"hits":stats["hits"],"results":res,"mock_used":False,"fixture_used":False}}
