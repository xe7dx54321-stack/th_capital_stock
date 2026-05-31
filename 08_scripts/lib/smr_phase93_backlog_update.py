import json,os
from datetime import datetime

def build_backlog_update():
    backlog = [
        {"rank":1,"gap":"order_contract_source","status":"partially_addressed","phase":"phase92_93","note":"order_text_done_structured_db_foundation_created"},
        {"rank":2,"gap":"customer_capex_source","status":"partially_addressed","phase":"phase93","note":"customer_capex_text_exploration_done"},
        {"rank":3,"gap":"supply_chain_source","status":"partially_addressed","phase":"phase93","note":"supply_chain_text_exploration_done"},
        {"rank":4,"gap":"structured_order_database","status":"foundation_created","phase":"phase93","note":"schema_and_db_path_created_needs_population"},
        {"rank":5,"gap":"product_pricing_source","status":"unchanged","phase":"phase94","note":"next_phase_target"},
        {"rank":6,"gap":"management_guidance_source","status":"unchanged","phase":"phase94","note":"next_phase_target"},
        {"rank":7,"gap":"300394_cninfo_resolution","status":"unchanged","phase":"phase95","note":"blocker_persists"},
        {"rank":8,"gap":"688041_valuation_pricing","status":"unchanged","phase":"phase96","note":"gap_persists"},
        {"rank":9,"gap":"peer_benchmark_hard_data","status":"unchanged","phase":"phase96","note":"not_addressed"},
        {"rank":10,"gap":"order_customer_supply_linkage_data","status":"foundation_created","phase":"phase93","note":"linkage_framework_built_needs_population"},
    ]
    return {"phase93_backlog_update":{
        "generated_at":datetime.now().isoformat(),
        "backlog_items":len(backlog),
        "phase94_recommendation":"product_pricing_and_management_guidance_hard_source",
        "backlog":backlog,
        "mock_used":False,"fixture_used":False
    }}
