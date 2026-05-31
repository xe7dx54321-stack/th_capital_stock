import json,os
from datetime import datetime

def run_quality_gate(evidence):
    records = evidence.get("phase92_order_evidence_extraction",{}).get("evidence_records",[])
    
    gate_results = []
    stats = {"passed":0,"review_required":0,"rejected":0}
    
    for rec in records:
        gate = {
            "ticker":rec["ticker"],
            "market":rec["market"],
            "gate_status":"passed",
            "checks":[]
        }
        
        for item in rec["evidence_items"]:
            check = {"evidence_type":item["evidence_type"],"status":"passed","issues":[]}
            
            # Check 1: source confidence
            if item["confidence"] == "low":
                check["issues"].append("low_confidence_evidence")
            
            # Check 2: blocked source
            if item["evidence_type"] == "source_blocked":
                check["status"] = "review_required"
                check["issues"].append("underlying_source_blocked")
            
            # Check 3: cannot_conclude violations
            forbidden = ["buy_or_sell_recommendation","target_price","position_sizing","confirmed_trade"]
            violations = [c for c in item.get("cannot_conclude",[]) if any(f in c for f in forbidden)]
            if violations:
                check["status"] = "rejected"
                check["issues"].append("trade_signal_violation")
            
            gate["checks"].append(check)
        
        # Determine overall status
        if any(c["status"]=="rejected" for c in gate["checks"]):
            gate["gate_status"] = "rejected"
            stats["rejected"] += 1
        elif any(c["status"]=="review_required" for c in gate["checks"]):
            gate["gate_status"] = "review_required"
            stats["review_required"] += 1
        else:
            stats["passed"] += 1
        
        gate_results.append(gate)
    
    return {"phase92_order_quality_gate":{
        "generated_at":datetime.now().isoformat(),
        "gate_summary":stats,
        "gate_results":gate_results,
        "mock_used":False,"fixture_used":False
    }}
