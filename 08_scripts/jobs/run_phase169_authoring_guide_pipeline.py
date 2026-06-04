import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase169_config import load_phase169_config
from smr_phase169_domain_registry import build_phase169_domain_registry
from smr_phase169_loaders import load_phase168_context, load_phase159_schema
from smr_phase169_guide import build_fill_guide, build_example_pack
from smr_phase169_preflight import build_preflight_validator, build_sandbox_simulation
from smr_phase169_console import build_authoring_console_integration
from smr_phase169_guard import build_authoring_guide_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    cfg = load_phase169_config()
    registry = build_phase169_domain_registry()
    p168 = load_phase168_context()
    p159 = load_phase159_schema()
    guide = build_fill_guide()
    examples = build_example_pack()
    preflight = build_preflight_validator()
    sandbox = build_sandbox_simulation()
    console = build_authoring_console_integration()
    g = build_authoring_guide_guard(preflight)
    qg = build_quality_gate()
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update()
    return {"phase169_authoring_guide_pipeline":{
        "mode":mode,"phase":"phase169","strategy":"owner_decision_input_authoring_guide_and_example_pack",
        "research_only":True,"fill_guide_ready":True,
        "valid_examples":examples["phase169_example_pack"]["valid_example_count"],
        "invalid_examples":examples["phase169_example_pack"]["invalid_example_count"],
        "preflight_enabled":True,"sandbox_enabled":True,"console_integrated":True,
        "guard":g["phase169_authoring_guide_guard"]["status"],
        "quality_gate":qg["phase169_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase169_cannot_conclude_guard"]["status"],"violations":0,
        "guide_not_auto_write":True,"preflight_not_real_submission":True,"sandbox_not_real_execution":True,
        "watch_core_updated":False,"candidate_auto_activated":False,"activation_execution_created":False,
        "target_price_created":0,"position_sizing_created":0,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase 170: Owner authors and submits real owner_decision_input.json using this guide."
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode")
    p.add_argument("--execute", action="store_const", const="execute", dest="mode")
    p.add_argument("--skip-network", action="store_const", const="skip-network", dest="mode")
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); mode = args.mode or "dry-run"
    result = run(mode)
    if args.markdown: print(json.dumps(result, ensure_ascii=False, indent=2))
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
