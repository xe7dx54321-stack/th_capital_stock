import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase93_customer_source_registry import build_customer_source_registry
from smr_phase93_supply_chain_source_registry import build_supply_chain_source_registry
from smr_phase93_entity_resolver import build_entity_resolver
from smr_phase93_customer_exploration import explore_customer_sources
from smr_phase93_supply_exploration import explore_supply_sources
from smr_phase93_evidence_extraction import extract_evidence
from smr_phase93_quality_gate import run_quality_gate
from smr_phase93_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase93_coverage_matrices import build_coverage_matrices
from smr_phase93_gap_closeout import build_gap_closeout
from smr_phase93_backlog_update import build_backlog_update
from smr_phase93_linkage_builder import build_linkage
from smr_phase93_structured_order_db import build_order_db_foundation

def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    
    c_reg=build_customer_source_registry()
    s_reg=build_supply_chain_source_registry()
    ent=build_entity_resolver()
    ce=explore_customer_sources(mode)
    se=explore_supply_sources(mode)
    ev=extract_evidence(ce,se)
    gate=run_quality_gate(ev)
    guard=run_cannot_conclude_guard(ev)
    cm=build_coverage_matrices(ce,se)
    gc=build_gap_closeout(cm)
    bl=build_backlog_update()
    lk=build_linkage(ce,se)
    odb=build_order_db_foundation(mode)
    
    summary={
        "customer_sources_registered":c_reg["phase93_customer_source_registry"]["customer_sources_registered"],
        "supply_sources_registered":s_reg["phase93_supply_chain_source_registry"]["supply_chain_sources_registered"],
        "entity_relations":ent["phase93_entity_resolver"]["total_customer_relations"]+ent["phase93_entity_resolver"]["total_supplier_relations"],
        "customer_hits":ce["phase93_customer_source_exploration"]["customer_capex_hits"],
        "supply_hits":se["phase93_supply_source_exploration"]["supply_chain_hits"],
        "customer_evidence":ev["phase93_evidence_extraction"]["customer_evidence_created"],
        "supply_evidence":ev["phase93_evidence_extraction"]["supply_evidence_created"],
        "gate_passed":gate["phase93_quality_gate"]["gate_summary"]["passed"],
        "guard_status":guard["phase93_cannot_conclude_guard"]["overall_status"],
        "customer_text_found":cm["phase93_customer_coverage_matrix"]["text_found"],
        "supply_text_found":cm["phase93_supply_coverage_matrix"]["text_found"],
        "blocked_tickers":cm["phase93_customer_coverage_matrix"]["blocked"],
        "linkage_count":lk["phase93_linkage_builder"]["total_customer_links"]+lk["phase93_linkage_builder"]["total_supply_links"],
        "order_db_schema":odb["phase93_structured_order_db_foundation"]["schema_written"],
        "phase94_recommendation":bl["phase93_backlog_update"]["phase94_recommendation"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price_created":0,"position_sizing_created":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
