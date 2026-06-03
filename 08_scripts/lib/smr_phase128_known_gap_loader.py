import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase127_gap_register import build_gap_register
from smr_phase127_blocker_register import build_blocker_register
def load_known_gaps():
 gaps=build_gap_register()
 blockers=build_blocker_register()
 return {"phase128_known_gap_loader":{"gaps":gaps["phase127_gap_register"],"blockers":blockers["phase127_blocker_register"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False}}
