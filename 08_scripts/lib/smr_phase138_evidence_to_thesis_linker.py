def build_evidence_to_thesis_linker():
 links={
  "688041.SH":{"thesis_id":"TH-688041-001","evidence_from":["Phase137:financial_data_confirmed","Phase137:valuation_derived_reviewed","Phase136:owner_deep_dive_request","Phase135:FB-OA-001","Phase132:valuation_hardening"],"evidence_type":"financial_valuation_mix","evidence_quality":"derived_estimates"},
  "NVDA":{"thesis_id":"TH-NVDA-001","evidence_from":["Phase137:financial_quality_confirmed","Phase137:AI_catalyst_active","Phase135:FB-TC-001","Phase133:seasonal_revenue_strengthened"],"evidence_type":"financial_quality","evidence_quality":"direct_observation"},
  "300394.SZ":{"thesis_id":"TH-300394-001","evidence_from":["Phase137:cninfo_still_blocked","Phase137:eastmoney_usable","Phase135:FB-SS-001","Phase131:alternative_source"],"evidence_type":"source_limitation","evidence_quality":"alternative_incomplete"}
 }
 return {"phase138_evidence_to_thesis_linker":{"links":links,"total":len(links),"all_research_only":True,"mock_used":False,"fixture_used":False}}
