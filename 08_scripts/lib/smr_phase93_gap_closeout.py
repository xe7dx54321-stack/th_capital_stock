import json,os
from datetime import datetime

def build_gap_closeout(coverage_matrices):
    c_matrix = coverage_matrices.get("phase93_customer_coverage_matrix",{}).get("coverage_rows",[])
    s_matrix = coverage_matrices.get("phase93_supply_coverage_matrix",{}).get("coverage_rows",[])
    
    items = []
    for cr,sr in zip(c_matrix, s_matrix):
        items.append({
            "ticker":cr["ticker"],
            "customer_capex_pre":"gap","customer_capex_post":cr["customer_capex_coverage_status"],
            "supply_chain_pre":"gap","supply_chain_post":sr["supply_chain_coverage_status"],
            "customer_gap_closed":False,"supply_gap_closed":False,
            "note":"text_exploration_complete_structured_data_still_gap",
            "next_action":"structured_customer_supply_database_integration"
        })
    
    return {"phase93_hard_data_gap_closeout":{
        "generated_at":datetime.now().isoformat(),
        "dimensions":["customer_capex","supply_chain"],
        "total_tickers":len(items),
        "customer_partial":sum(1 for i in items if "text_found" in i["customer_capex_post"]),
        "supply_partial":sum(1 for i in items if "text_found" in i["supply_chain_post"]),
        "gap_items":items,
        "summary":"customer_capex_and_supply_chain_text_exploration_complete;structured_data_remains_gap",
        "mock_used":False,"fixture_used":False
    }}
