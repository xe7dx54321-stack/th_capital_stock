import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase160_config import load_phase160_config
    from smr_phase160_generators import generate_all_examples
    from smr_phase160_sandbox import run_sandbox_validation, aggregate_sandbox_results
    from smr_phase160_expectation_checker import check_all_expectations
    from smr_phase160_guard import build_sandbox_guard
    from smr_phase160_quality_gate import build_quality_gate
    from smr_phase160_cannot_conclude_guard import build_cannot_conclude_guard

    config = load_phase160_config()
    pack = generate_all_examples()
    examples = pack["phase160_example_pack"]["examples"]
    results = [run_sandbox_validation(ex) for ex in examples]
    aggregator = aggregate_sandbox_results(results)
    expectations = check_all_expectations(examples, results)
    guard = build_sandbox_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()

    output = {
        "phase160_dashboard": {
            "phase": "phase160",
            "strategy": config.get("strategy", ""),
            "research_only": config.get("research_only", True),
            "example_pack": {
                "total_examples": pack["phase160_example_pack"]["total_examples"],
                "valid_examples": pack["phase160_example_pack"]["valid_examples"],
                "invalid_examples": pack["phase160_example_pack"]["invalid_examples"]
            },
            "sandbox": {
                "total_safe": aggregator["phase160_sandbox_aggregator"]["total_safe"],
                "total_invalid": aggregator["phase160_sandbox_aggregator"]["total_invalid"],
                "total_quarantine": aggregator["phase160_sandbox_aggregator"]["total_quarantine"],
                "total_preview": aggregator["phase160_sandbox_aggregator"]["total_preview"],
                "total_execution": 0
            },
            "expectations": {
                "all_match": expectations["phase160_expectation_checker_aggregate"]["all_expectations_match"]
            },
            "guard": guard["phase160_sandbox_guard"]["status"],
            "quality_gate": quality["phase160_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase160_cannot_conclude_guard"]["status"],
            "violations": guard["phase160_sandbox_guard"]["violations"],
            "safety": {
                "real_owner_input_overwrite_allowed": config.get("real_owner_input_overwrite_allowed", False),
                "activation_execution_allowed": config.get("activation_execution_allowed", False),
                "simulation_only": config.get("simulation_only", True),
                "mock_used": False,
                "fixture_used": False,
                "raw_saved": False,
                "ocr_used": False,
                "browser_automation_used": False,
                "pending_created": 0,
                "paper_order_created": 0,
                "real_trade_created": 0,
                "target_price_created": 0,
                "position_sizing_created": 0
            }
        }
    }

    if mode == "markdown":
        d = output["phase160_dashboard"]
        print("# Phase 160 Dashboard: Owner Decision Example Pack & Safe Input Sandbox")
        print()
        print(f"| Metric | Value |")
        print(f"|--------|-------|")
        print(f"| Research only | {d['research_only']} |")
        print(f"| Total examples | {d['example_pack']['total_examples']} |")
        print(f"| Valid examples | {d['example_pack']['valid_examples']} |")
        print(f"| Invalid examples | {d['example_pack']['invalid_examples']} |")
        print(f"| Total safe | {d['sandbox']['total_safe']} |")
        print(f"| Total invalid | {d['sandbox']['total_invalid']} |")
        print(f"| Total quarantine | {d['sandbox']['total_quarantine']} |")
        print(f"| Total execution | {d['sandbox']['total_execution']} |")
        print(f"| Expectations match | {d['expectations']['all_match']} |")
        print(f"| Guard | {d['guard']} |")
        print(f"| Quality gate | {d['quality_gate']} |")
        print(f"| Cannot-conclude guard | {d['cannot_conclude_guard']} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
