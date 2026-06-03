import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_szse_disclosure_fallback import build_szse_disclosure_fallback
from smr_phase130_irm_interaction_fallback import build_irm_interaction_fallback
from smr_phase130_company_ir_loader import build_company_ir_loader

def build_alternative_disclosure_registry():
    szse=build_szse_disclosure_fallback()["phase130_szse_disclosure_fallback"]["sources"]
    irm=build_irm_interaction_fallback()["phase130_irm_interaction_fallback"]["sources"]
    ir=build_company_ir_loader()["phase130_company_ir_loader"]["sources"]
    all_sources=szse+irm+ir
    return {"phase130_alternative_disclosure_registry":{"total":len(all_sources),"ticker":"300394.SZ","coverage_type":"alternative_disclosure_sources_for_cninfo_blocked_ticker","sources":all_sources,"all_free_no_key":True,"mock_used":False,"fixture_used":False}}
