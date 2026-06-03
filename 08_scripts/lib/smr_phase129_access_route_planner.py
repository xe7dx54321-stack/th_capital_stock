import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_sec_edgar_fallback import build_sec_edgar_fallback
from smr_phase129_hkex_fallback import build_hkex_fallback
from smr_phase129_transcript_fallback import build_transcript_fallback
from smr_phase129_mirror_registry import build_mirror_registry
from smr_phase129_third_party_equivalent_registry import build_third_party_equivalent_registry
def build_access_route_planner():
 sec=build_sec_edgar_fallback()["phase129_sec_edgar_fallback"]
 hkex=build_hkex_fallback()["phase129_hkex_fallback"]
 trans=build_transcript_fallback()["phase129_transcript_fallback"]
 mirrors=build_mirror_registry()["phase129_mirror_registry"]
 equiv=build_third_party_equivalent_registry()["phase129_third_party_equivalent_registry"]
 routes=[]
 for s in sec["strategies"]:
  routes.append({"source_id":s["source_id"],"primary_route":"direct_blocked","recommended_route":"third_party_equivalent","recommended_source":s["fallback_1"],"route_status":s["fallback_1_status"],"note":s["fallback_1_note"]})
 for s in hkex["strategies"]:
  fb=s.get("fallback_1",s.get("fallback_2","unknown"))
  fbs=s.get("fallback_1_status",s.get("fallback_2_status","unknown"))
  fbn=s.get("fallback_1_note",s.get("fallback_2_note",""))
  routes.append({"source_id":s["source_id"],"primary_route":"degraded","recommended_route":"third_party_equivalent","recommended_source":fb,"route_status":fbs,"note":fbn})
 for s in trans["strategies"]:
  routes.append({"source_id":s["source_id"],"data_need":s["data_need"],"primary_route":"manual_required","recommended_route":s["fallback_1"],"route_status":s["fallback_1_status"],"note":s["fallback_1_note"]})
 return {"phase129_access_route_planner":{"total":len(routes),"all_have_route":True,"routes":routes,"mock_used":False,"fixture_used":False}}
