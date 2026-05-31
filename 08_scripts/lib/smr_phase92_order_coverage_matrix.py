import json,os
from datetime import datetime

def build_order_coverage_matrix(exploration_results):
    exploration = exploration_results.get("phase92_order_source_exploration",{})
    ticker_results = exploration.get("ticker_results",[])
    
    coverage_rows = []
    for tr in ticker_results:
        has_hits = tr["keyword_hits"] > 0
        is_blocked = tr.get("blocked",False)
        
        if is_blocked:
            status = "blocked"
        elif has_hits:
            status = "order_text_found"
        else:
            status = "no_order_text_found"
        
        coverage_rows.append({
            "ticker":tr["ticker"],
            "market":tr["market"],
            "order_contract_coverage_status":status,
            "sources_attempted":len(tr["source_attempts"]),
            "text_units_collected":tr["total_text_units"],
            "order_keyword_hits":tr["keyword_hits"],
            "blocked":is_blocked
        })
    
    covered = sum(1 for r in coverage_rows if r["order_contract_coverage_status"]=="order_text_found")
    blocked = sum(1 for r in coverage_rows if r["order_contract_coverage_status"]=="blocked")
    no_text = sum(1 for r in coverage_rows if r["order_contract_coverage_status"]=="no_order_text_found")
    
    return {"phase92_order_source_coverage_matrix":{
        "generated_at":datetime.now().isoformat(),
        "tickers_total":len(coverage_rows),
        "order_text_found":covered,
        "blocked":blocked,
        "no_order_text_found":no_text,
        "coverage_rows":coverage_rows,
        "mock_used":False,"fixture_used":False
    }}
