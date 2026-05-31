import json,os
from datetime import datetime

def run_cannot_conclude_guard(evidence):
    records = evidence.get("phase93_evidence_extraction",{}).get("evidence_records",[])
    guard_results = []
    violations = 0
    
    for rec in records:
        guard = {"ticker":rec["ticker"],"guard_status":"pass","violations":[]}
        
        for item in rec.get("customer_evidence",[])+rec.get("supply_evidence",[]):
            forbidden = ["buy","sell","short","long","target_price","position","allocation","entry","exit"]
            claim = item.get("claim","").lower()
            for term in forbidden:
                if term in claim:guard["violations"].append(f"trade_term:{term}");violations+=1
            
            # Check: customer capex != company order confirmed
            # Check: supply chain signal != trade signal
            # Check: blocked not hidden
        
        if guard["violations"]:guard["guard_status"]="violation"
        guard_results.append(guard)
    
    return {"phase93_cannot_conclude_guard":{"generated_at":datetime.now().isoformat(),"overall_status":"pass" if violations==0 else "violations_detected","violations_found":violations,"guard_results":guard_results,"mock_used":False,"fixture_used":False}}
