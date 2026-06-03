import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_pending_network_closeout import build_pending_network_closeout

def build_backlog_update(skip_network=False):
    closeout=build_pending_network_closeout(skip_network)["phase128_pending_network_closeout"]
    return {"phase128_backlog_update":{"phase128_status":"external_source_probe_complete","pending_network_before":closeout["pending_network_before"],"pending_network_after":closeout["pending_network_after"],"next_phase":"phase129_300394_blocker_resolution_or_new_capability","deprecated_forever":["paper_order","paper_trade","paper_position","paper_pnl","broker","live_trading","target_price","position_sizing","profit_loss","return_tracking"],"mock_used":False,"fixture_used":False}}
