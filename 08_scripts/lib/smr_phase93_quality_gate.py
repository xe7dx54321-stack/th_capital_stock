import json,os
from datetime import datetime

def run_quality_gate(evidence):
    records = evidence.get("phase93_evidence_extraction",{}).get("evidence_records",[])
    gate_results = []
    stats = {"passed":0,"review_required":0,"rejected":0}
    
    for rec in records:
        gate = {"ticker":rec["ticker"],"gate_status":"passed","checks":[]}
        
        for item in rec.get("customer_evidence",[])+rec.get("supply_evidence",[]):
            check = {"evidence_type":item["evidence_type"],"status":"passed","issues":[]}
            if item["confidence"]=="low":check["issues"].append("low_confidence")
            if item["evidence_type"]=="source_blocked":check["status"]="review_required";check["issues"].append("source_blocked")
            if "buy_signal" in str(item.get("cannot_conclude",[])):check["status"]="rejected";check["issues"].append("trade_violation")
            gate["checks"].append(check)
        
        if any(c["status"]=="rejected" for c in gate["checks"]):gate["gate_status"]="rejected";stats["rejected"]+=1
        elif any(c["status"]=="review_required" for c in gate["checks"]):gate["gate_status"]="review_required";stats["review_required"]+=1
        else:stats["passed"]+=1
        gate_results.append(gate)
    
    return {"phase93_quality_gate":{"generated_at":datetime.now().isoformat(),"gate_summary":stats,"gate_results":gate_results,"mock_used":False,"fixture_used":False}}
