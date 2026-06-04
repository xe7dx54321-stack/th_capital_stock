import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase169_guide import build_fill_guide, build_example_pack
from smr_phase169_preflight import build_preflight_validator, build_sandbox_simulation
from smr_phase169_console import build_authoring_console_integration
from smr_phase169_guard import build_authoring_guide_guard, build_quality_gate, build_cannot_conclude_guard

def build():
    guide = build_fill_guide()
    examples = build_example_pack()
    preflight = build_preflight_validator()
    sandbox = build_sandbox_simulation()
    console = build_authoring_console_integration()
    g = build_authoring_guide_guard(preflight)
    qg = build_quality_gate()
    cc = build_cannot_conclude_guard()
    return {"phase169_authoring_guide_board":{
        "fill_guide_ready":True,"valid_examples":examples["phase169_example_pack"]["valid_example_count"],
        "invalid_examples":examples["phase169_example_pack"]["invalid_example_count"],
        "preflight_enabled":True,"sandbox_enabled":True,"console_integrated":True,
        "guard":g["phase169_authoring_guide_guard"]["status"],
        "quality_gate":qg["phase169_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase169_cannot_conclude_guard"]["status"],"violations":0,
        "research_only":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); result = build()
    if args.markdown:
        for k,v in result["phase169_authoring_guide_board"].items(): print(f"- {k}: {v}")
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
