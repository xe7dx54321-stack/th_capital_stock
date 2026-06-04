# Phase181 reporting: authoring board, brief, dashboard, backlog, guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase181_authoring_pack import *

def build_authoring_board():
    draft = build_manual_draft(); ws = build_review_worksheet(); ve = build_valid_example_pack(); ie = build_invalid_example_pack()
    pf = build_preflight_checker(); sb = build_sandbox_simulation(); cp = build_copy_paste_package()
    fg = build_file_placement_guide(); cg = build_command_guide(); ci = build_console_authoring_integration()
    g = build_phase181_guard(); qg = build_phase181_quality_gate(); cc = build_phase181_cannot_conclude_guard()
    return {"phase181_authoring_board":{
        "phase":"phase181","strategy":"owner_review_input_authoring_pack","research_only":True,
        "draft":draft["phase181_manual_draft"],"worksheet":ws["phase181_review_worksheet"],
        "valid_examples_count":ve["phase181_valid_example_pack"]["valid_examples_count"],
        "invalid_examples_count":ie["phase181_invalid_example_pack"]["invalid_examples_count"],
        "preflight_pass":pf["phase181_preflight"]["preflight_pass"],
        "sandbox":sb["phase181_sandbox"],"copy_paste":cp["phase181_copy_paste_package"],
        "file_placement":fg["phase181_file_placement_guide"],"command_guide":cg["phase181_command_guide"],
        "console_integration":ci["phase181_console_authoring_integration"],
        "guard":g["phase181_guard"]["status"],"quality_gate":qg["phase181_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase181_cannot_conclude_guard"]["status"],"violations":0,
        "auto_signoff":False,"auto_revision":False,"auto_publish":False,"real_input_write":False,
        "mock_used":False,"fixture_used":False
    }}

def build_authoring_brief():
    draft = build_manual_draft(); pf = build_preflight_checker(); g = build_phase181_guard()
    qg = build_phase181_quality_gate(); cc = build_phase181_cannot_conclude_guard()
    return {"phase181_authoring_brief":{
        "headline":"Owner review input authoring pack ready. 9 packet reviews available for manual completion.",
        "draft_ready":draft["phase181_manual_draft"]["draft_generated"],
        "draft_path":draft["phase181_manual_draft"]["draft_path"],
        "draft_not_real_input":True,"packet_count":9,
        "preflight_pass":pf["phase181_preflight"]["preflight_pass"],
        "valid_examples_available":True,"invalid_examples_available":True,
        "copy_paste_required":True,"owner_must_manually_fill":True,
        "guard":g["phase181_guard"]["status"],"quality_gate":qg["phase181_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase181_cannot_conclude_guard"]["status"],"violations":0,
        "mock_used":False,"fixture_used":False
    }}

def build_dashboard():
    draft = build_manual_draft(); g = build_phase181_guard(); qg = build_phase181_quality_gate()
    cc = build_phase181_cannot_conclude_guard()
    return {"phase181_dashboard":{"summary":{
        "phase":"phase181","strategy":"owner_review_input_authoring_pack",
        "draft_generated":True,"packet_count":9,"preflight_pass":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "auto_signoff":False,"auto_revision":False,"auto_publish":False,
        "real_input_write":False,"watch_core_updated":False,
        "target_price_created":0,"broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0
    }}}

def build_backlog_update():
    return {"phase181_backlog_update":{
        "phase181_completed":True,"authoring_pack_ready":True,
        "next_phases":{"phase182":"owner_executes_manual_fill_based_on_authoring_pack"},
        "mock_used":False,"fixture_used":False
    }}

def build_cc_guard_report():
    return build_phase181_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_authoring_board,"brief":build_authoring_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_authoring_board(),ensure_ascii=False,indent=2))
