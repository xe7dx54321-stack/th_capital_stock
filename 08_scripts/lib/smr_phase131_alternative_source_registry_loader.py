import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_alternative_disclosure_registry import build_alternative_disclosure_registry
def load_alternative_source_registry():
 sources=build_alternative_disclosure_registry()["phase130_alternative_disclosure_registry"]["sources"]
 financial=[s for s in sources if s["type"] in ["official_exchange","financial_data_aggregator"]]
 metadata=[s for s in sources if s["type"] in ["investor_relations","company_ir"]]
 return {"phase131_alternative_source_registry_loader":{"total":len(sources),"financial_sources":len(financial),"metadata_sources":len(metadata),"financial_sources":financial,"metadata_sources":metadata,"ticker":"300394.SZ","mock_used":False,"fixture_used":False}}
