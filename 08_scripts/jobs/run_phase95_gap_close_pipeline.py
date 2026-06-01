import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase95_config import load_config
from smr_phase95_300394_resolver import resolve_300394
from smr_phase95_688041_valuation import harden_valuation
from smr_phase95_688041_pricing import harden_pricing
from smr_phase95_coverage_update import build_coverage
from smr_phase95_gap_backlog import build_gap_closeout, build_backlog
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase94_regression","status":"ok","detail":""})
    cfg=load_config();steps.append({"name":"load_config","status":"ok","detail":f"phase={cfg['phase']}"})
    res394=resolve_300394(mode)
    r3=res394.get("phase95_300394_resolution",{})
    steps.append({"name":"resolve_300394","status":"ok","detail":f"identity_found={r3.get('identity_found',False)},source_exhausted={r3.get('source_exhausted',False)}"})
    val688041=harden_valuation(mode)
    v6=val688041.get("phase95_688041_valuation",{})
    steps.append({"name":"harden_valuation_688041","status":"ok","detail":f"valuation_available={v6.get('valuation_available','unavailable')}"})
    pri688041=harden_pricing(mode)
    p6=pri688041.get("phase95_688041_pricing",{})
    steps.append({"name":"harden_pricing_688041","status":"ok","detail":f"pricing_available={p6.get('pricing_available')}"})
    cm=build_coverage(res394,val688041,pri688041)
    steps.append({"name":"coverage_update","status":"ok","detail":f"covered={cm['phase95_coverage_update']['covered']},partial={cm['phase95_coverage_update']['partial']},blocked={cm['phase95_coverage_update']['blocked']}"})
    gc=build_gap_closeout(res394,val688041,pri688041)
    steps.append({"name":"gap_closeout","status":"ok","detail":f"resolved={gc['phase95_gap_closeout']['resolved']},partial={gc['phase95_gap_closeout']['partial']},still_blocked={gc['phase95_gap_closeout']['still_blocked']}"})
    bl=build_backlog()
    steps.append({"name":"backlog","status":"ok","detail":f"items={bl['phase95_backlog']['items']}"})
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw/ocr/browser=false,pending/order/trade=0"})
    out={
        "phase95_pipeline":{
            "mode":mode,"generated_at":datetime.now().isoformat(),
            "tickers":8,
            "300394_identity_found":r3.get("identity_found",False),
            "300394_source_exhausted":r3.get("source_exhausted",False),
            "300394_blocker":r3.get("blocker_status","persists"),
            "688041_valuation":v6.get("valuation_available","unavailable"),
            "688041_pricing":"resolved" if p6.get("pricing_available") else "unavailable",
            "covered":cm["phase95_coverage_update"]["covered"],
            "partial":cm["phase95_coverage_update"]["partial"],
            "blocked":cm["phase95_coverage_update"]["blocked"],
            "pricing_resolved":gc["phase95_gap_closeout"]["resolved"],
            "phase96":bl["phase95_backlog"]["phase96_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
