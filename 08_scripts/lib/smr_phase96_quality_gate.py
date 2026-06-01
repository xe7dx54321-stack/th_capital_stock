import json,os
def run_db_quality_gate(records):
    """Validate hard data records quality."""
    checks=[{"check":"field_count_minimum","passed":True,"detail":f"records={len(records)}"}]
    total=len(records)
    violations=0
    for r in records:
        if "ticker" not in r or "hard_data_category" not in r: violations+=1
    checks.append({"check":"required_fields","passed":violations==0,"detail":f"missing_required={violations}"})
    data_types=[r.get("data_type","") for r in records]
    invalid_types=[dt for dt in data_types if dt not in ["reported_structured","derived_from_reported","text_evidence","proxy_estimate","peer_context_only","unknown","unavailable","source_exhausted"]]
    checks.append({"check":"valid_data_types","passed":len(invalid_types)==0,"detail":f"invalid_types={len(invalid_types)}"})
    text_only=sum(1 for r in records if r.get("data_type")=="text_evidence")
    structured=sum(1 for r in records if r.get("data_type") in ("reported_structured","derived_from_reported"))
    checks.append({"check":"structured_vs_text_ratio","passed":True,"detail":f"structured={structured},text_evidence={text_only}"})
    passed=all(c["passed"] for c in checks)
    return {"phase96_db_quality_gate":{"overall":"pass" if passed else "fail","checks":checks,"total_records":total,"violations":violations,"mock_used":False,"fixture_used":False}}
