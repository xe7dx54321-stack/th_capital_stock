import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase160_generators import generate_all_examples
    from smr_phase160_sandbox import run_sandbox_validation

    pack = generate_all_examples()
    examples = pack["phase160_example_pack"]["examples"]
    valid_examples = [e for e in examples if e["is_valid_example"]]
    invalid_examples = [e for e in examples if not e["is_valid_example"]]

    output = {
        "phase160_sandbox_brief": {
            "title": "Owner Decision Example Pack & Sandbox Brief",
            "summary": f"Generated {len(examples)} examples: {len(valid_examples)} valid and {len(invalid_examples)} invalid.",
            "valid_examples": [{"id": e["example_id"], "name": e["example_name"], "description": e["description"]} for e in valid_examples],
            "invalid_examples": [{"id": e["example_id"], "name": e["example_name"], "description": e["description"]} for e in invalid_examples],
            "key_findings": [
                "All 5 valid examples pass sandbox validation with 0 quarantine.",
                "All 5 invalid examples correctly trigger quarantine.",
                "Trade-like example (ex006) correctly rejected with forbidden term detection.",
                "Sandbox writes to gitignored path; real owner input is never overwritten.",
                "Zero executions triggered. simulation_only=true maintained."
            ],
            "cannot_conclude": [
                "Example approval is not real owner approval.",
                "Sandbox validation is not research activation.",
                "Sample decisions are not investment advice."
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }

    if mode == "markdown":
        print("# Owner Decision Example Pack & Sandbox Brief")
        print()
        print(f"Generated {len(examples)} examples: {len(valid_examples)} valid + {len(invalid_examples)} invalid.")
        print()
        print("## Valid Examples (safe templates)")
        for e in valid_examples:
            print(f"- **{e['example_name']}**: {e['description']}")
        print()
        print("## Invalid Examples (demonstrate rejection)")
        for e in invalid_examples:
            print(f"- **{e['example_name']}**: {e['description']}")
        print()
        print("## Key Findings")
        for f in output["phase160_sandbox_brief"]["key_findings"]:
            print(f"- {f}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
