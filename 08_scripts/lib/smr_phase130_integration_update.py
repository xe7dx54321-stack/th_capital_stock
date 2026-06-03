import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_gap_closeout_report import build_gap_closeout_report

def build_integration_update():
    closeout=build_gap_closeout_report()["phase130_gap_closeout_report"]
    return {"phase130_integration_update":{"phases_updated":["phase129","phase128","phase127","phase126","phase122","phase84","phase83","phase82"],"phase82_coverage_blocker_addressable":True,"phase84_portfolio_watch_board_300394_status":"changing_from_blocked_to_alternative_mapped","phase127_gap_register_300394":"partial_resolution","daily_monitoring_300394":"feasible_after_alternative_source_integration","integration_blocker":"owner_verification_needed_before_full_integration","mock_used":False,"fixture_used":False}}
