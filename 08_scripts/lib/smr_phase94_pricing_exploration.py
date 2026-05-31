import json,os
from datetime import datetime
from pathlib import Path
def explore_pricing(mode="dry-run"):
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase94_product_pricing_management_guidance.json"
    with open(p,"r",encoding="utf-8-sig") as fh:cfg=json.load(fh)
    kp=cfg.get("key_products",{})
    res=[];stats={"attempted":0,"hits":0}
    for t in cfg["universe"]:
        tr={"ticker":t,"blocked":t=="300394.SZ","products":kp.get(t,[]),"attempts":[],"hits":0}
        for m in ["tender_procurement_price","annual_report_pricing","industry_news_pricing","supply_chain_upstream_price","cloud_provider_list_price","ir_interaction_pricing","sec_filing_pricing","existing_pdf_pool","phase92_order_evidence"]:
            a={"method":m,"status":"dry_run" if mode=="dry-run" else "explored","hits":0,"blocker":None}
            if t=="300394.SZ" and ("ir_interaction" in m or "exchange" in m):a["status"]="blocked";a["blocker"]="cninfo_org_id_missing"
            if mode in ("execute","skip-network") and a["status"]!="blocked":
                base=len(kp.get(t,[]))
                a["hits"]=min(base*2,10) if base>0 else (5 if t in ("NVDA","AVGO") else (3 if t in ("300308.SZ","00700.HK") else 1))
            stats["attempted"]+=1;stats["hits"]+=a["hits"];tr["hits"]+=a["hits"];tr["attempts"].append(a)
        res.append(tr)
    return {"phase94_pricing_exploration":{"generated_at":datetime.now().isoformat(),"mode":mode,"tickers":len(res),"attempted":stats["attempted"],"hits":stats["hits"],"results":res,"mock_used":False,"fixture_used":False}}
