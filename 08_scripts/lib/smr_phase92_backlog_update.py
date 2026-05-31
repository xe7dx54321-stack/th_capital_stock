import json,os
from datetime import datetime

def build_backlog_update():
    backlog = [
        {"rank":1,"gap":"order_contract_source","pre_phase92_status":"highest_priority_gap","post_phase92_status":"partially_addressed_exploration_complete","phase_target":"phase92_complete","note":"order_text_exploration_done;structured_order_contract_database_still_gap"},
        {"rank":2,"gap":"customer_capex_source","pre_phase92_status":"highest_priority_gap","post_phase92_status":"unchanged","phase_target":"phase93","note":"not_addressed_in_phase92"},
        {"rank":3,"gap":"supply_chain_source","pre_phase92_status":"highest_priority_gap","post_phase92_status":"unchanged","phase_target":"phase93","note":"not_addressed_in_phase92"},
        {"rank":4,"gap":"product_pricing_source","pre_phase92_status":"high_priority","post_phase92_status":"unchanged","phase_target":"phase94","note":"not_addressed_in_phase92"},
        {"rank":5,"gap":"management_guidance_source","pre_phase92_status":"high_priority","post_phase92_status":"unchanged","phase_target":"phase95","note":"not_addressed_in_phase92"},
        {"rank":6,"gap":"300394_cninfo_resolution","pre_phase92_status":"high_priority","post_phase92_status":"unchanged","phase_target":"phase95","note":"blocker_persists"},
        {"rank":7,"gap":"688041_valuation_pricing","pre_phase92_status":"medium_priority","post_phase92_status":"unchanged","phase_target":"phase96","note":"not_addressed_in_phase92"},
        {"rank":8,"gap":"industry_news_hard_data","pre_phase92_status":"medium_priority","post_phase92_status":"partially_addressed","phase_target":"phase96","note":"order_exploration_adds_industry_context"},
        {"rank":9,"gap":"peer_benchmark_hard_data","pre_phase92_status":"medium","post_phase92_status":"unchanged","phase_target":"phase96","note":"not_addressed"},
        {"rank":10,"gap":"structured_order_database","pre_phase92_status":"not_listed","post_phase92_status":"new_gap_identified","phase_target":"phase93","note":"phase92_found_text_but_not_structured_order_data;new_requirement_emerged"},
    ]
    
    return {"phase92_backlog_update":{
        "generated_at":datetime.now().isoformat(),
        "backlog_items":len(backlog),
        "phase93_recommendation":"focus_on_customer_capex_supply_chain_structured_order_database",
        "backlog":backlog,
        "mock_used":False,"fixture_used":False
    }}
