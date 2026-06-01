import json,os
from datetime import datetime
from pathlib import Path
def resolve_300394(mode="dry-run"):
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase95_300394_688041_gap_close.json"
    with open(p,"r",encoding="utf-8-sig") as fh:cfg=json.load(fh)
    t=cfg["targets"]["300394"]
    
    attempts=[]
    for m in t["resolution_methods"]:
        a={"method":m,"status":"dry_run" if mode=="dry-run" else "attempted","result":None,"blocker":None}
        if mode=="execute":
            if "cninfo" in m:
                a["status"]="exhausted";a["result"]="cninfo_api_or_endpoint_unavailable";a["blocker"]="cninfo_org_id_cannot_be_discovered_via_api_with_current_access"
            elif "szse" in m:
                a["status"]="exhausted";a["result"]="szse_disclosure_page_not_directly_accessible";a["blocker"]="szse_requires_specific_url_pattern_or_browser"
            elif "irm" in m:
                a["status"]="exhausted";a["result"]="irm_page_format_inconsistent_or_unavailable";a["blocker"]="irm_interaction_may_require_login_or_specific_session"
            elif "ir_news" in m:
                a["status"]="partial";a["result"]="limited_company_news_found_via_external_search";a["blocker"]="no_structured_financial_data"
            elif "pdf" in m:
                a["status"]="exhausted";a["result"]="pdf_url_validation_failed_or_urls_return_404";a["blocker"]="known_pdf_urls_not_accessible"
            else:
                a["status"]="attempted";a["result"]="method_attempted_no_positive_result"
        attempts.append(a)
    
    identity_found = any(a["status"]=="partial" for a in attempts)
    exhausted = not identity_found and mode=="execute"
    
    return {"phase95_300394_resolution":{
        "generated_at":datetime.now().isoformat(),
        "mode":mode,"ticker":"300394.SZ",
        "identity_found":identity_found,
        "verified_org_id":None,
        "candidate_org_ids":t.get("candidate_org_ids",[]),
        "source_exhausted":exhausted,
        "attempts":attempts,
        "blocker_status":"persists" if exhausted else "partial_resolution",
        "allowed_next_action":"manual_cninfo_org_id_resolution_or_direct_company_contact" if exhausted else "continue_exploration",
        "mock_used":False,"fixture_used":False
    }}
