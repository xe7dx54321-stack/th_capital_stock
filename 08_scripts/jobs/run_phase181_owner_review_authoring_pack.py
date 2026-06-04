# Phase181 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase181_authoring_pack import *

def run_pipeline(mode="dry-run"):
    draft = build_manual_draft()
    ws = build_review_worksheet()
    ve = build_valid_example_pack()
    ie = build_invalid_example_pack()
    pf = build_preflight_checker()
    sb = build_sandbox_simulation()
    em = build_expectation_matcher()
    cp = build_copy_paste_package()
    fg = build_file_placement_guide()
    cg = build_command_guide()
    ci = build_console_authoring_integration()
    g = build_phase181_guard()
    qg = build_phase181_quality_gate()
    cc = build_phase181_cannot_conclude_guard()

    d = draft["phase181_manual_draft"]
    return {"phase181_owner_review_authoring_pack_pipeline":{
        "mode":mode,"phase":"phase181","strategy":"owner_review_input_authoring_pack",
        "research_only":True,"packet_count":d["packet_count"],
        "draft_generated":d["draft_generated"],"draft_is_template":d["draft_is_template"],
        "draft_not_real_input":d["draft_not_real_input"],
        "worksheet_count":ws["phase181_review_worksheet"]["worksheet_count"],
        "valid_examples":ve["phase181_valid_example_pack"]["valid_examples_count"],
        "invalid_examples":ie["phase181_invalid_example_pack"]["invalid_examples_count"],
        "preflight_pass":pf["phase181_preflight"]["preflight_pass"],
        "preflight_issues":pf["phase181_preflight"]["issues_found"],
        "sandbox_ok":sb["phase181_sandbox"]["sandbox_checked"],
        "expectations_match":em["phase181_expectation_matcher"]["expectations_all_match"],
        "copy_paste_ready":cp["phase181_copy_paste_package"]["package_generated"],
        "file_placement_ready":fg["phase181_file_placement_guide"]["guide_generated"],
        "command_guide_ready":cg["phase181_command_guide"]["guide_generated"],
        "console_integration_ready":True,
        "guard":g["phase181_guard"]["status"],"quality_gate":qg["phase181_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase181_cannot_conclude_guard"]["status"],
        "violations":qg["phase181_quality_gate"]["violations"],
        "auto_signoff":False,"auto_revision":False,"auto_publish":False,
        "real_input_write":False,"real_input_overwrite":False,
        "owner_must_manually_fill":True,"draft_path_ignored":True,
        "watch_core_updated":False,"target_price_created":0,"position_sizing_created":0,
        "trade_recommendation_created":0,"broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase182: Owner executes manual fill based on authoring pack, then runs Phase179 validation pipeline."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
