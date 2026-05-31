import json,os
from datetime import datetime

def build_coverage_matrices(customer_exploration, supply_exploration):
    cust = customer_exploration.get("phase93_customer_source_exploration",{}).get("ticker_results",[])
    supp = supply_exploration.get("phase93_supply_source_exploration",{}).get("ticker_results",[])
    
    customer_rows = []
    supply_rows = []
    
    for ct,st in zip(cust, supp):
        is_blocked = ct.get("blocked",False)
        
        c_stat = "blocked" if is_blocked else ("customer_capex_text_found" if ct["total_hits"]>0 else "no_text_found")
        customer_rows.append({"ticker":ct["ticker"],"customer_capex_coverage_status":c_stat,"hits":ct["total_hits"],"key_customers":len(ct.get("key_customers",[])),"blocked":is_blocked})
        
        s_stat = "blocked" if is_blocked else ("supply_chain_text_found" if st["total_hits"]>0 else "no_text_found")
        supply_rows.append({"ticker":st["ticker"],"supply_chain_coverage_status":s_stat,"hits":st["total_hits"],"key_suppliers":len(st.get("key_suppliers",[])),"blocked":is_blocked})
    
    c_found = sum(1 for r in customer_rows if r["customer_capex_coverage_status"]=="customer_capex_text_found")
    s_found = sum(1 for r in supply_rows if r["supply_chain_coverage_status"]=="supply_chain_text_found")
    
    return {
        "phase93_customer_coverage_matrix":{"tickers_total":len(customer_rows),"text_found":c_found,"blocked":sum(1 for r in customer_rows if r["blocked"]),"coverage_rows":customer_rows},
        "phase93_supply_coverage_matrix":{"tickers_total":len(supply_rows),"text_found":s_found,"blocked":sum(1 for r in supply_rows if r["blocked"]),"coverage_rows":supply_rows}
    }
