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
    res394=resolve_300394(mode)
    val688041=harden_valuation(mode)
    pri688041=harden_pricing(mode)
    cm=build_coverage(res394,val688041,pri688041)
    gc=build_gap_closeout(res394,val688041,pri688041)
    bl=build_backlog()
    r3=res394.get("phase95_300394_resolution",{})
    v6=val688041.get("phase95_688041_valuation",{})
    p6=pri688041.get("phase95_688041_pricing",{})
    summary={
        "phase":"phase95","generated_at":datetime.now().isoformat(),
        "300394_identity_found":False,
        "300394_source_exhausted":r3.get("source_exhausted",False),
        "300394_blocker":r3.get("blocker_status","persists"),
        "688041_valuation":v6.get("valuation_available","unavailable"),
        "688041_pricing":"resolved" if p6.get("pricing_available") else "unavailable",
        "covered":cm["phase95_coverage_update"]["covered"],
        "partial":cm["phase95_coverage_update"]["partial"],
        "blocked":cm["phase95_coverage_update"]["blocked"],
        "pricing_resolved":gc["phase95_gap_closeout"]["resolved"],
        "gap_partial":gc["phase95_gap_closeout"]["partial"],
        "still_blocked":gc["phase95_gap_closeout"]["still_blocked"],
        "phase96_recommendation":bl["phase95_backlog"]["phase96_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
