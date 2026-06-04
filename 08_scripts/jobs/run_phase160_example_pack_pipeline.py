import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def run(mode="dry-run"):
    from smr_phase160_config import load_phase160_config
    from smr_phase160_domain_registry import build_phase160_domain_registry
    from smr_phase160_loaders import load_phase159_context, load_phase158_context, load_phase156_context, load_phase153_context
    from smr_phase160_example_schema import build_example_schema
    from smr_phase160_generators import generate_all_examples
    from smr_phase160_example_manifest import build_example_manifest
    from smr_phase160_sandbox import write_sandbox_input, run_sandbox_validation, aggregate_sandbox_results
    from smr_phase160_expectation_checker import check_all_expectations
    from smr_phase160_compatibility_checker import check_phase159_compatibility
    from smr_phase160_copy_guide import build_copy_guide
    from smr_phase160_cookbook import build_cookbook
    from smr_phase160_guard import build_sandbox_guard
    from smr_phase160_quality_gate import build_quality_gate
    from smr_phase160_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase160_backlog import build_backlog_update

    config = load_phase160_config()

    domain = build_phase160_domain_registry()
    ctx159 = load_phase159_context()
    ctx158 = load_phase158_context()
    ctx156 = load_phase156_context()
    ctx153 = load_phase153_context()
    schema = build_example_schema()

    pack = generate_all_examples()
    examples = pack["phase160_example_pack"]["examples"]
    manifest = build_example_manifest()

    results = []
    for ex in examples:
        if mode == "execute":
            write_sandbox_input(ex)
        results.append(run_sandbox_validation(ex))

    aggregator = aggregate_sandbox_results(results)
    expectations = check_all_expectations(examples, results)
    compatibility = check_phase159_compatibility()
    copy_guide = build_copy_guide()
    cookbook = build_cookbook()
    guard = build_sandbox_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()
    backlog = build_backlog_update()

    output = {
        "phase160_example_pack_pipeline": {
            "mode": mode,
            "phase": "phase160",
            "strategy": config.get("strategy", ""),
            "example_pack_generated": True,
            "total_examples": pack["phase160_example_pack"]["total_examples"],
            "valid_examples": pack["phase160_example_pack"]["valid_examples"],
            "invalid_examples": pack["phase160_example_pack"]["invalid_examples"],
            "sandbox_total_safe": aggregator["phase160_sandbox_aggregator"]["total_safe"],
            "sandbox_total_invalid": aggregator["phase160_sandbox_aggregator"]["total_invalid"],
            "sandbox_total_quarantine": aggregator["phase160_sandbox_aggregator"]["total_quarantine"],
            "sandbox_total_execution": 0,
            "expectations_all_match": expectations["phase160_expectation_checker_aggregate"]["all_expectations_match"],
            "phase159_compatible": compatibility["phase160_compatibility_checker"]["phase159_compatible"],
            "guard": guard["phase160_sandbox_guard"]["status"],
            "quality_gate": quality["phase160_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase160_cannot_conclude_guard"]["status"],
            "violations": guard["phase160_sandbox_guard"]["violations"],
            "copy_guide_generated": True,
            "cookbook_generated": True,
            "domain_registry_generated": True,
            "example_manifest_generated": True,
            "sandbox_input_written": mode == "execute",
            "sandbox_path_ignored": True,
            "real_owner_input_overwritten": False,
            "watch_core_updated": False,
            "candidate_auto_activated": False,
            "tier_update_executed": False,
            "activation_execution_created": False,
            "mock_used": False,
            "fixture_used": False,
            "raw_saved": False,
            "ocr_used": False,
            "browser_automation_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0,
            "trade_recommendation_created": 0,
            "broker_api_called": False,
            "next_phase_recommendation": backlog["phase160_backlog"]["next_phase_recommendation"]
        }
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output

if __name__ == "__main__":
    mode = "dry-run"
    if "--execute" in sys.argv:
        mode = "execute"
    elif "--skip-network" in sys.argv:
        mode = "skip-network"
    run(mode)
