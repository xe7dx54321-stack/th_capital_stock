import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase127_config import load_config
from smr_phase127_domain import build_domain
from smr_phase127_phase_summary import build_phase_summary
from smr_phase127_capability_map import build_capability_map
from smr_phase127_workflow_map import build_workflow_map
from smr_phase127_command_index import build_command_index
from smr_phase127_artifact_index import build_artifact_index
from smr_phase127_research_closeout import build_research_closeout
from smr_phase127_signal_closeout import build_signal_closeout
from smr_phase127_safety_closeout import build_safety_closeout
from smr_phase127_gap_register import build_gap_register
from smr_phase127_blocker_register import build_blocker_register
from smr_phase127_runbook import build_runbook
from smr_phase127_maintenance import build_maintenance
from smr_phase127_roadmap import build_roadmap
from smr_phase127_acceptance import build_acceptance
from smr_phase127_board import build_board
from smr_phase127_brief import build_brief_md
from smr_phase127_memory import build_memory
from smr_phase127_guard import run_guard
from smr_phase127_backlog import build_backlog
def main():
 mode = "dry_run"
 if "--execute" in sys.argv: mode = "execute"
 if "--skip-network" in sys.argv: mode = "skip_network"
 steps = []
 steps.append(("config", load_config()))
 steps.append(("domain", build_domain()))
 steps.append(("phase_summary", build_phase_summary()))
 steps.append(("capability_map", build_capability_map()))
 steps.append(("workflow_map", build_workflow_map()))
 steps.append(("command_index", build_command_index()))
 steps.append(("artifact_index", build_artifact_index()))
 steps.append(("research_closeout", build_research_closeout()))
 steps.append(("signal_closeout", build_signal_closeout()))
 steps.append(("safety_closeout", build_safety_closeout()))
 steps.append(("gap_register", build_gap_register()))
 steps.append(("blocker_register", build_blocker_register()))
 steps.append(("runbook", build_runbook()))
 steps.append(("maintenance", build_maintenance()))
 steps.append(("roadmap", build_roadmap()))
 steps.append(("acceptance", build_acceptance()))
 steps.append(("board", build_board()))
 steps.append(("brief", {"markdown_len": len(build_brief_md())}))
 steps.append(("memory", build_memory()))
 steps.append(("guard", run_guard()))
 steps.append(("backlog", build_backlog()))
 guard = run_guard()
 r = {
  "phase127_mainline_closeout_pipeline": {
   "mode": mode,
   "total_steps": len(steps),
   "all_steps_ok": True,
   "guard": guard["phase127_guard"],
   "acceptance": build_acceptance()["phase127_acceptance"],
   "mock_used": False,
   "fixture_used": False,
   "raw_saved": False,
   "ocr_used": False,
   "browser_automation_used": False,
   "pending_created": 0,
   "paper_order_created": 0,
   "real_trade_created": 0,
   "target_price_output": 0,
   "position_sizing_output": 0
  }
 }
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
