import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_pricing_registry import build_pricing_registry
from smr_phase94_guidance_registry import build_guidance_registry
from smr_phase94_entity_resolver import build_entity_resolver
from smr_phase94_pricing_exploration import explore_pricing
from smr_phase94_guidance_exploration import explore_guidance
from smr_phase94_evidence import extract_evidence
from smr_phase94_quality_gate import run_gate
from smr_phase94_guard import run_guard
from smr_phase94_coverage import build_coverage
from smr_phase94_gap_backlog import build_gap_closeout, build_backlog
from smr_phase94_linkage import build_linkage
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    pr=build_pricing_registry();gr=build_guidance_registry()
    ent=build_entity_resolver()
    pe=explore_pricing(mode);ge=explore_guidance(mode)
    ev=extract_evidence(pe,ge);gate=run_gate(ev);guard=run_guard(ev)
    cm=build_coverage(pe,ge);gc=build_gap_closeout(cm);bl=build_backlog()
    lk=build_linkage(pe,ge)
    summary={
        "pricing_sources":pr["phase94_pricing_registry"]["pricing_sources"],
        "guidance_sources":gr["phase94_guidance_registry"]["guidance_sources"],
        "products_mapped":ent["phase94_entity_resolver"]["total_products_mapped"],
        "pricing_hits":pe["phase94_pricing_exploration"]["hits"],
        "guidance_hits":ge["phase94_guidance_exploration"]["hits"],
        "pricing_evidence":ev["phase94_evidence"]["pricing_evidence"],
        "guidance_evidence":ev["phase94_evidence"]["guidance_evidence"],
        "gate_passed":gate["phase94_gate"]["summary"]["passed"],
        "guard_status":guard["phase94_guard"]["overall"],
        "pricing_text_found":cm["phase94_pricing_coverage"]["found"],
        "guidance_text_found":cm["phase94_guidance_coverage"]["found"],
        "blocked":cm["phase94_pricing_coverage"]["blocked"],
        "linkage_count":lk["phase94_linkage"]["pricing_links"]+lk["phase94_linkage"]["guidance_links"],
        "phase95":bl["phase94_backlog"]["phase95_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
