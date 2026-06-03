import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_disclosure_coverage_classifier import classify_disclosure_coverage
from smr_phase130_resolution_decision_report import build_resolution_decision_report
def load_phase130_resolution():
 closeout=build_gap_closeout_report()["phase130_gap_closeout_report"]
 coverage=classify_disclosure_coverage()["phase130_disclosure_coverage_classifier"]
 decision=build_resolution_decision_report()["phase130_resolution_decision_report"]
 return {"phase131_phase130_resolution_loader":{"closeout":closeout,"coverage":coverage,"decision":decision,"owner_assumed_confirmed":True,"ready_for_integration":True,"mock_used":False,"fixture_used":False}}
