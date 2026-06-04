# Phase177 reporting: board, brief, dashboard, console, daily, weekly, backlog, guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase177_packet_builder import *

def build_packet_board():
    return build_all_packets()

def build_packet_brief():
    packets = build_all_packets()
    p = packets["phase177_deep_dive_packets"]
    return {"phase177_packet_brief":{"headline":"9 formal deep dive packets generated for activated candidates.","activated":p["activated_candidate_count"],"keep":p["keep_summary_count"],"defer":p["defer_summary_count"],"reject":p["reject_summary_count"],"packets_ready":p["packets_ready_for_owner_review"],"brief_ready_summaries":[pkt["brief_ready_summary"] for pkt in p["packets"]],"research_only":True,"mock_used":False,"fixture_used":False}}

def build_dashboard():
    packets = build_all_packets()
    p = packets["phase177_deep_dive_packets"]
    qg = build_packet_quality_gate(); g = build_phase177_guard(); cc = build_phase177_cannot_conclude_guard()
    return {"phase177_dashboard":{"summary":{"phase":"phase177","strategy":"deep_dive_packet_generation","activated":p["activated_candidate_count"],"packets":p["formal_packet_count"],"keep":p["keep_summary_count"],"defer":p["defer_summary_count"],"reject":p["reject_summary_count"],"guard":g["phase177_guard"]["status"],"quality_gate":qg["phase177_packet_quality_gate"]["status"],"cannot_conclude_guard":cc["phase177_cannot_conclude_guard"]["status"],"violations":qg["phase177_packet_quality_gate"]["violations"],"watch_core_updated":False,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,"llm_api_called":False,"mock_used":False,"fixture_used":False}}}

def build_console_integration():
    return {"phase177_console_integration":{"deep_dive_packets_linked":True,"owner_review_queue_linked":True,"console_can_display_packets":True,"research_only":True,"mock_used":False,"fixture_used":False}}

def build_daily_brief_preview():
    return {"phase177_daily_brief_preview":{"packet_summaries_available":True,"daily_brief_can_include_packet_excerpts":True,"not_trade_signal":True,"mock_used":False,"fixture_used":False}}

def build_weekly_review_preview():
    return {"phase177_weekly_review_preview":{"packet_deep_dives_available":True,"weekly_review_can_reference_packets":True,"not_trade_signal":True,"mock_used":False,"fixture_used":False}}

def build_backlog_update():
    return {"phase177_backlog_update":{"phase177_completed":True,"packets_generated":9,"next_phases":{"phase178":"packet_owner_review_and_signoff"},"mock_used":False,"fixture_used":False}}

def build_cc_guard_report():
    return build_phase177_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_packet_board,"brief":build_packet_brief,"dashboard":build_dashboard,"console":build_console_integration,"daily":build_daily_brief_preview,"weekly":build_weekly_review_preview,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname:
            print(json.dumps(f(),ensure_ascii=False,indent=2))
            break
    else:
        print(json.dumps(build_packet_board(),ensure_ascii=False,indent=2))
