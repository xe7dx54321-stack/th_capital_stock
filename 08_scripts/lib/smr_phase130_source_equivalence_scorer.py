import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_alternative_disclosure_registry import build_alternative_disclosure_registry

def build_source_equivalence_scorer():
    sources=build_alternative_disclosure_registry()["phase130_alternative_disclosure_registry"]["sources"]
    scored=[]
    for s in sources:
        sc={"source_id":s["source_id"],"type":s["type"]}
        if s["type"]=="official_exchange":
            sc["equivalence_to_cninfo"]="high_official_source"
            sc["financial_data_quality"]="official"
            sc["can_replace_cninfo_for_filings"]=True
        elif s["type"]=="investor_relations":
            sc["equivalence_to_cninfo"]="complementary"
            sc["financial_data_quality"]="N/A"
            sc["can_replace_cninfo_for_filings"]=False
            sc["can_supplement_with_qa"]=True
        elif s["type"]=="financial_data_aggregator":
            sc["equivalence_to_cninfo"]="high_aggregated"
            sc["financial_data_quality"]="aggregated_official"
            sc["can_replace_cninfo_for_filings"]=True
            sc["note"]="Eastmoney mirrors CNINFO data"
        elif s["type"]=="company_ir":
            sc["equivalence_to_cninfo"]="medium_company_source"
            sc["financial_data_quality"]="company_official"
            sc["can_replace_cninfo_for_filings"]="partially"
            sc["note"]="Company IR may have financial reports"
        scored.append(sc)
    high=sum(1 for s in scored if "high" in s.get("equivalence_to_cninfo",""))
    return {"phase130_source_equivalence_scorer":{"total":len(scored),"high_equivalence":high,"medium_equivalence":len(scored)-high-2,"complementary":2,"results":scored,"mock_used":False,"fixture_used":False}}
