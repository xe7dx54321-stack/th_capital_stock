import json,os
from datetime import datetime

def extract_evidence(customer_exploration, supply_exploration):
    cust = customer_exploration.get("phase93_customer_source_exploration",{}).get("ticker_results",[])
    supp = supply_exploration.get("phase93_supply_source_exploration",{}).get("ticker_results",[])
    
    evidence_list = []
    for ct,st in zip(cust, supp):
        ev = {"ticker":ct["ticker"],"blocked":ct.get("blocked",False),"customer_evidence":[],"supply_evidence":[]}
        
        # Customer evidence
        if ct["total_hits"]>0 and not ct.get("blocked"):
            ev["customer_evidence"].append({
                "evidence_type":"customer_capex_signal_found",
                "claim":"customer_capex_or_procurement_related_text_identified",
                "limitation":"customer_capex_signal_does_not_confirm_specific_order_or_revenue",
                "cannot_conclude":["specific_order_value","revenue_timing","market_share_change","buy_signal"],
                "source_trace":"customer_financial_and_procurement_sources",
                "confidence":"medium",
                "mock_used":False
            })
        else:
            ev["customer_evidence"].append({
                "evidence_type":"no_customer_capex_signal","claim":"no_customer_capex_text_identified","limitation":"exploration_not_exhaustive","cannot_conclude":["competitor_has_customer_orders","market_demand_weak"],"confidence":"low","mock_used":False
            })
        
        # Supply evidence
        if st["total_hits"]>0 and not st.get("blocked"):
            ev["supply_evidence"].append({
                "evidence_type":"supply_chain_signal_found",
                "claim":"supply_chain_capacity_or_delivery_related_text_identified",
                "limitation":"supply_chain_signal_does_not_confirm_specific_company_benefit",
                "cannot_conclude":["company_specific_benefit","revenue_impact","market_share_gain","buy_signal"],
                "source_trace":"supply_chain_disclosure_and_news_sources",
                "confidence":"medium",
                "mock_used":False
            })
        else:
            ev["supply_evidence"].append({
                "evidence_type":"no_supply_chain_signal","claim":"no_supply_chain_text_identified","limitation":"exploration_not_exhaustive","cannot_conclude":["supply_chain_healthy","no_bottlenecks"],"confidence":"low","mock_used":False
            })
        
        # Blocker evidence
        if ct.get("blocked"):
            ev["customer_evidence"].append({"evidence_type":"source_blocked","claim":"customer_source_blocked_by_300394_cninfo_blocker","limitation":"underlying_disclosure_source_unavailable","cannot_conclude":["customer_demand","order_status"],"confidence":"confirmed_blocker","mock_used":False})
            ev["supply_evidence"].append({"evidence_type":"source_blocked","claim":"supply_source_blocked_by_300394_cninfo_blocker","limitation":"underlying_disclosure_source_unavailable","cannot_conclude":["supply_status"],"confidence":"confirmed_blocker","mock_used":False})
        
        evidence_list.append(ev)
    
    return {"phase93_evidence_extraction":{
        "generated_at":datetime.now().isoformat(),
        "customer_evidence_created":sum(1 for e in evidence_list if any(it["evidence_type"]=="customer_capex_signal_found" for it in e["customer_evidence"])),
        "supply_evidence_created":sum(1 for e in evidence_list if any(it["evidence_type"]=="supply_chain_signal_found" for it in e["supply_evidence"])),
        "evidence_records":evidence_list,
        "mock_used":False,"fixture_used":False
    }}
