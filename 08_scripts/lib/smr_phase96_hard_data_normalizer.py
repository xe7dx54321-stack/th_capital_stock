import json,os
def normalize_hard_data_records(records):
    """Normalize and classify hard data records."""
    from smr_phase96_config import get_field_data_types
    valid_types=get_field_data_types()
    normalized=[]
    for r in records:
        n=dict(r)
        dt=n.get("data_type","text_evidence")
        if dt not in valid_types: n["data_type"]="text_evidence"
        n["normalization_status"]="normalized"
        n["normalization_note"]=f"data_type_classified_as_{dt}"
        normalized.append(n)
    return {"phase96_hard_data_normalization":{"records_normalized":len(normalized),"records":normalized,"mock_used":False,"fixture_used":False}}
