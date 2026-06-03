def build_thesis_entity_registry():
 theses={
  "688041.SH":{"thesis_id":"TH-688041-001","thesis":"688041 benefits from domestic semiconductor substitution but valuation inputs are derived estimates","status":"thesis_supported","market":"CN_A","sector":"Semiconductor"},
  "NVDA":{"thesis_id":"TH-NVDA-001","thesis":"NVDA is the primary beneficiary of AI GPU capex cycle with strong financial quality","status":"thesis_strengthened","market":"US","sector":"AI/GPU"},
  "AVGO":{"thesis_id":"TH-AVGO-001","thesis":"AVGO benefits from AI networking and ASIC demand with stable semiconductor infrastructure","status":"thesis_supported","market":"US","sector":"Semiconductor/Infra"},
  "09988.HK":{"thesis_id":"TH-09988-001","thesis":"Alibaba cloud revenue acceleration driven by AI adoption","status":"thesis_observed","market":"HK","sector":"E-commerce/Cloud"},
  "00700.HK":{"thesis_id":"TH-00700-001","thesis":"Tencent gaming cycle and advertising recovery support stable growth","status":"thesis_observed","market":"HK","sector":"Internet/Gaming"},
  "300308.SZ":{"thesis_id":"TH-300308-001","thesis":"Zhongji Innolight benefits from optical communication demand growth","status":"thesis_context_supported","market":"CN_A","sector":"Optical Communication"},
  "300394.SZ":{"thesis_id":"TH-300394-001","thesis":"TFC Optical operates in optical devices with alternative data source limitations","status":"thesis_unconfirmed","market":"CN_A","sector":"Optical Devices","risk":"cninfo_org_id_missing"},
  "002230.SZ":{"thesis_id":"TH-002230-001","thesis":"iFLYTEK AI/software business maintains stable trend","status":"thesis_context_supported","market":"CN_A","sector":"AI/Software"}
 }
 return {"phase138_thesis_entity_registry":{"theses":theses,"total":len(theses),"all_research_only":True,"mock_used":False,"fixture_used":False}}
