import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_third_party_equivalent_registry import build_third_party_equivalent_registry

def build_equivalence_scorer():
    equivalents=build_third_party_equivalent_registry()["phase129_third_party_equivalent_registry"]["equivalents"]
    scored=[]
    for e in equivalents:
        s={"official_source":e["official_source"],"equivalent_id":e["equivalent_id"]}
        if e["equivalent_status"]=="available" and e["quality"]=="high":
            s["score"]="high_equivalence"
            s["usable_as_primary"]=True
        elif e["equivalent_status"]=="available" and e["quality"]=="medium":
            s["score"]="medium_equivalence"
            s["usable_as_primary"]=False
            s["usable_as_supplementary"]=True
        else:
            s["score"]="low_or_no_equivalence"
            s["usable_as_primary"]=False
            s["usable_as_supplementary"]=False
        s["limitation"]=e["limitation"]
        scored.append(s)
    high=sum(1 for s in scored if s["score"]=="high_equivalence")
    return {"phase129_equivalence_scorer":{"total":len(scored),"high_equivalence":high,"medium_equivalence":len(scored)-high-1,"low_equivalence":1,"results":scored,"mock_used":False,"fixture_used":False}}
