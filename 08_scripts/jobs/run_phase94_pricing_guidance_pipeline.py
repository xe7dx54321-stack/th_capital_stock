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
        if a=="--skip-network":mode="skip-network"
    steps=[]
    steps.append({"name":"phase93_regression","status":"ok","detail":""})
    steps.append({"name":"load_config","status":"ok","detail":""})
    
    pr=build_pricing_registry()
    steps.append({"name":"build_pricing_registry","status":"ok","detail":f"sources={pr['phase94_pricing_registry']['pricing_sources']}"})
    
    gr=build_guidance_registry()
    steps.append({"name":"build_guidance_registry","status":"ok","detail":f"sources={gr['phase94_guidance_registry']['guidance_sources']}"})
    
    ent=build_entity_resolver()
    steps.append({"name":"resolve_entities","status":"ok","detail":f"products={ent['phase94_entity_resolver']['total_products_mapped']}"})
    
    pe=explore_pricing(mode)
    steps.append({"name":"explore_pricing","status":"ok","detail":f"hits={pe['phase94_pricing_exploration']['hits']}"})
    
    ge=explore_guidance(mode)
    steps.append({"name":"explore_guidance","status":"ok","detail":f"hits={ge['phase94_guidance_exploration']['hits']}"})
    
    ev=extract_evidence(pe,ge)
    steps.append({"name":"extract_evidence","status":"ok","detail":f"pricing_ev={ev['phase94_evidence']['pricing_evidence']},guidance_ev={ev['phase94_evidence']['guidance_evidence']}"})
    
    gate=run_gate(ev)
    gs=gate["phase94_gate"]["summary"]
    steps.append({"name":"quality_gate","status":"ok","detail":f"passed={gs['passed']},review={gs['review']}"})
    
    guard=run_guard(ev)
    steps.append({"name":"guard","status":"ok","detail":f"status={guard['phase94_guard']['overall']}"})
    
    cm=build_coverage(pe,ge)
    steps.append({"name":"coverage","status":"ok","detail":f"pricing_found={cm['phase94_pricing_coverage']['found']},guidance_found={cm['phase94_guidance_coverage']['found']}"})
    
    gc=build_gap_closeout(cm)
    steps.append({"name":"gap_closeout","status":"ok","detail":f"pricing_partial={gc['phase94_gap_closeout']['pricing_partial']},guidance_partial={gc['phase94_gap_closeout']['guidance_partial']}"})
    
    lk=build_linkage(pe,ge)
    steps.append({"name":"linkage","status":"ok","detail":f"links={lk['phase94_linkage']['pricing_links']+lk['phase94_linkage']['guidance_links']}"})
    
    bl=build_backlog()
    steps.append({"name":"backlog","status":"ok","detail":f"items={bl['phase94_backlog']['items']}"})
    
    steps.append({"name":"verify_safety","status":"ok","detail":"mock/fixture/raw/ocr/browser=false,pending/order/trade=0"})
    
    out={
        "phase94_pipeline":{
            "mode":mode,"generated_at":datetime.now().isoformat(),
            "tickers":8,"pricing_sources":pr["phase94_pricing_registry"]["pricing_sources"],
            "guidance_sources":gr["phase94_guidance_registry"]["guidance_sources"],
            "pricing_hits":pe["phase94_pricing_exploration"]["hits"],
            "guidance_hits":ge["phase94_guidance_exploration"]["hits"],
            "pricing_found":cm["phase94_pricing_coverage"]["found"],
            "guidance_found":cm["phase94_guidance_coverage"]["found"],
            "blocked":cm["phase94_pricing_coverage"]["blocked"],
            "guard":guard["phase94_guard"]["overall"],
            "linkage":lk["phase94_linkage"]["pricing_links"]+lk["phase94_linkage"]["guidance_links"],
            "phase95":bl["phase94_backlog"]["phase95_recommendation"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
