import json,os
def build_backlog_update():
    """Update Phase 91-95 backlog status."""
    items=[
        {"r":1,"gap":"300394_cninfo","status":"exhausted_blocked","phase":"phase95","phase96_note":"blocker_preserved_no_new_resolution"},
        {"r":2,"gap":"688041_valuation","status":"partial","phase":"phase95","phase96_note":"partial_valuation_in_hard_data_db"},
        {"r":3,"gap":"688041_pricing","status":"resolved","phase":"phase95","phase96_note":"pricing_data_in_hard_data_db"},
        {"r":4,"gap":"structured_order_db","status":"foundation","phase":"phase93","phase96_note":"order_evidence_populated_to_hard_data_db"},
        {"r":5,"gap":"customer_capex_db","status":"foundation","phase":"phase93","phase96_note":"customer_capex_evidence_populated"},
        {"r":6,"gap":"supply_chain_db","status":"foundation","phase":"phase93","phase96_note":"supply_chain_evidence_populated"},
        {"r":7,"gap":"product_pricing_db","status":"foundation","phase":"phase94","phase96_note":"product_pricing_evidence_populated"},
        {"r":8,"gap":"management_guidance_db","status":"foundation","phase":"phase94","phase96_note":"management_guidance_evidence_populated"},
        {"r":9,"gap":"peer_benchmark_hard_data","status":"established","phase":"phase96","phase96_note":"peer_benchmark_matrix_and_source_resolver_built"},
        {"r":10,"gap":"structured_db_population","status":"completed","phase":"phase96","phase96_note":"hard_data_db_populated_with_all_phase92_95_evidence"},
    ]
    return {"phase96_backlog_update":{"items":len(items),"rows":items,"phase97_recommendation":"automated_db_refresh_and_incremental_hard_data_update","mock_used":False,"fixture_used":False}}
