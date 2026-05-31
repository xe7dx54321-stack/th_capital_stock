import json,os
from datetime import datetime

def extract_order_evidence(classified_signals):
    signals = classified_signals.get("phase92_order_signal_classifier",{}).get("classified_signals",[])
    
    evidence_list = []
    for ticker_sigs in signals:
        ticker_evidence = {
            "ticker":ticker_sigs["ticker"],
            "market":ticker_sigs["market"],
            "blocked":ticker_sigs.get("blocked",False),
            "evidence_items":[]
        }
        
        if ticker_sigs["signals_classified"] > 0:
            ticker_evidence["evidence_items"].append({
                "evidence_type":"order_activity_observed",
                "claim":"order_or_contract_related_text_found_in_disclosure_or_news",
                "limitation":"order_text_presence_does_not_confirm_revenue_recognition_or_contract_execution",
                "cannot_conclude":[
                    "order_value_precise",
                    "revenue_timing_confirmed",
                    "customer_identified",
                    "competitive_win_vs_competitor",
                    "buy_or_sell_recommendation"
                ],
                "source_trace":"keyword_scan_in_disclosure_text",
                "confidence":"medium",
                "mock_used":False
            })
        else:
            ticker_evidence["evidence_items"].append({
                "evidence_type":"no_order_evidence_found",
                "claim":"no_order_or_contract_related_text_found_in_explored_sources",
                "limitation":"exploration_was_not_exhaustive_due_to_source_availability_or_network_constraints",
                "cannot_conclude":["competitor_has_orders","company_has_no_orders"],
                "source_trace":"all_explored_sources",
                "confidence":"low",
                "mock_used":False
            })
        
        if ticker_sigs.get("blocked"):
            ticker_evidence["evidence_items"].append({
                "evidence_type":"source_blocked",
                "claim":"order_source_exploration_blocked_by_underlying_data_source_blocker",
                "limitation":"300394_cninfo_org_id_missing_prevents_disclosure_access",
                "cannot_conclude":["order_status","contract_status"],
                "source_trace":"cninfo_blocked",
                "confidence":"confirmed_blocker",
                "mock_used":False
            })
        
        evidence_list.append(ticker_evidence)
    
    return {"phase92_order_evidence_extraction":{
        "generated_at":datetime.now().isoformat(),
        "order_evidence_created":sum(1 for e in evidence_list if any(it["evidence_type"]=="order_activity_observed" for it in e["evidence_items"])),
        "evidence_records":evidence_list,
        "mock_used":False,"fixture_used":False
    }}
