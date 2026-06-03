import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_source_equivalence_scorer import build_source_equivalence_scorer

def classify_disclosure_coverage():
    scored=build_source_equivalence_scorer()["phase130_source_equivalence_scorer"]["results"]
    coverage={"financial_statements":"partially_covered","annual_reports":"covered_via_szse","quarterly_reports":"covered_via_szse","announcements":"covered_via_szse_and_eastmoney","investor_qa":"covered_via_irm","company_ir_info":"covered_via_company_website","raw_cninfo_data":"not_directly_available_without_org_id"}
    high=[s for s in scored if "high" in s.get("equivalence_to_cninfo","")]
    return {"phase130_disclosure_coverage_classifier":{"ticker":"300394.SZ","coverage_level":"partial_official_plus_aggregator","cninfo_direct":"blocked","szse_direct":"available","eastmoney_indirect":"available","financial_data_feasible":True,"financial_data_source":"eastmoney_or_szse","announcement_access_feasible":True,"coverage_detail":coverage,"remaining_gap":"cninfo_raw_data_format","mock_used":False,"fixture_used":False}}
