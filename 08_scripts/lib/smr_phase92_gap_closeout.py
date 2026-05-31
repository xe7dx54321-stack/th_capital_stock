import json,os
from datetime import datetime

def build_gap_closeout(coverage_matrix, exploration_results):
    matrix = coverage_matrix.get("phase92_order_source_coverage_matrix",{})
    rows = matrix.get("coverage_rows",[])
    exploration = exploration_results.get("phase92_order_source_exploration",{})
    
    closeout_items = []
    for row in rows:
        item = {
            "ticker":row["ticker"],
            "market":row["market"],
            "gap_dimension":"order_contract",
            "pre_phase92_status":"gap",
            "post_phase92_status":row["order_contract_coverage_status"]
        }
        
        if row["order_contract_coverage_status"] == "order_text_found":
            item["closeout_note"] = "order_text_found_in_disclosure_or_news;quality_is_keyword_based_not_structured_contract_data"
        elif row["order_contract_coverage_status"] == "blocked":
            item["closeout_note"] = "gap_persists_due_to_underlying_source_blocker"
        else:
            item["closeout_note"] = "order_text_not_found_in_explored_sources;gap_remains_for_structured_order_data"
        
        item["gap_fully_closed"] = False  # Keyword text != structured order data
        item["next_action"] = "structured_order_contract_database_integration" if not row.get("blocked") else "resolve_underlying_blocker_first"
        
        closeout_items.append(item)
    
    fully_closed = sum(1 for c in closeout_items if c["gap_fully_closed"])
    partially_addressed = sum(1 for c in closeout_items if c["post_phase92_status"]=="order_text_found")
    
    return {"phase92_order_hard_data_gap_closeout":{
        "generated_at":datetime.now().isoformat(),
        "gap_dimension":"order_contract",
        "total_tickers":len(closeout_items),
        "fully_closed":fully_closed,
        "partially_addressed":partially_addressed,
        "still_gap":len(closeout_items)-fully_closed,
        "closeout_items":closeout_items,
        "summary":"order_text_exploration_complete;structured_order_data_remains_gap_for_all_tickers",
        "mock_used":False,"fixture_used":False
    }}
