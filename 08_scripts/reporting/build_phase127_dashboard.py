import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase127_acceptance import build_acceptance
from smr_phase127_guard import run_guard
from smr_phase127_backlog import build_backlog
from smr_phase127_gap_register import build_gap_register
from smr_phase127_blocker_register import build_blocker_register
from smr_phase127_research_closeout import build_research_closeout
def main():
 accept = build_acceptance()
 guard = run_guard()
 backlog = build_backlog()
 gaps = build_gap_register()
 blockers = build_blocker_register()
 research = build_research_closeout()
 r = {
  "phase127_dashboard": {
   "phase111_126_mainline": "closed",
   "phase111_126_mainline_accepted": accept["phase127_acceptance"]["all_met"],
   "acceptance": accept["phase127_acceptance"],
   "guard": guard["phase127_guard"],
   "backlog": backlog["phase127_backlog"],
   "gaps": gaps["phase127_gap_register"],
   "blockers": blockers["phase127_blocker_register"],
   "research": research["phase127_research_closeout"],
   "mock_used": False,
   "fixture_used": False
  }
 }
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
