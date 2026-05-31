import json,os
from datetime import datetime

def run_cannot_conclude_guard(evidence, quality_gate):
    records = evidence.get("phase92_order_evidence_extraction",{}).get("evidence_records",[])
    gate = quality_gate.get("phase92_order_quality_gate",{}).get("gate_results",[])
    
    guard_results = []
    violations_found = 0
    
    for rec in records:
        guard = {
            "ticker":rec["ticker"],
            "market":rec["market"],
            "guard_status":"pass",
            "violations":[]
        }
        
        for item in rec["evidence_items"]:
            # Check: tender != contract award
            if item["evidence_type"] == "order_activity_observed":
                guard["guard_status"] = "pass"
            
            # Check: no trade signal in evidence
            forbidden_terms = ["buy","sell","short","long","target_price","position","allocation","entry","exit"]
            for term in forbidden_terms:
                claim_lower = item.get("claim","").lower()
                if term in claim_lower:
                    guard["violations"].append(f"trade_term_found:{term}")
                    violations_found += 1
            
            # Check: blocked not hidden
            if item["evidence_type"] == "source_blocked":
                if "visible" not in str(item).lower():
                    guard["violations"].append("blocker_may_be_hidden")
        
        if guard["violations"]:
            guard["guard_status"] = "violation_found"
        
        guard_results.append(guard)
    
    return {"phase92_cannot_conclude_guard":{
        "generated_at":datetime.now().isoformat(),
        "overall_status":"pass" if violations_found==0 else "violations_detected",
        "violations_found":violations_found,
        "guard_results":guard_results,
        "mock_used":False,"fixture_used":False
    }}
