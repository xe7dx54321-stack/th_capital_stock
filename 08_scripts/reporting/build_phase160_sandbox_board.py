import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase160_generators import generate_all_examples
    from smr_phase160_sandbox import run_sandbox_validation
    from smr_phase160_expectation_checker import check_all_expectations

    pack = generate_all_examples()
    examples = pack["phase160_example_pack"]["examples"]
    results = [run_sandbox_validation(ex) for ex in examples]
    expectation = check_all_expectations(examples, results)

    rows = []
    for ex, vr in zip(examples, results):
        v = vr["phase160_sandbox_validation"]
        rows.append({
            "example_id": ex["example_id"],
            "example_name": ex["example_name"],
            "is_valid_example": ex["is_valid_example"],
            "is_trade_like": ex["is_trade_like"],
            "safe_count": v["safe_count"],
            "invalid_count": v["invalid_count"],
            "quarantine_count": v["quarantine_count"],
            "preview_count": v["preview_count"],
            "execution_count": 0,
            "expectations_match": None
        })

    ec = expectation.get("phase160_expectation_checker_aggregate", {})
    for r in ec.get("results", []):
        ecr = r.get("phase160_expectation_checker", {})
        eid = ecr.get("example_id", "")
        for row in rows:
            if row["example_id"] == eid:
                row["expectations_match"] = ecr.get("expectations_match")

    output = {
        "phase160_sandbox_board": {
            "total_examples": len(rows),
            "valid_examples": sum(1 for r in rows if r["is_valid_example"]),
            "invalid_examples": sum(1 for r in rows if not r["is_valid_example"]),
            "trade_like_examples": sum(1 for r in rows if r["is_trade_like"]),
            "total_safe": sum(r["safe_count"] for r in rows),
            "total_invalid": sum(r["invalid_count"] for r in rows),
            "total_quarantine": sum(r["quarantine_count"] for r in rows),
            "total_execution": 0,
            "all_expectations_match": ec.get("all_expectations_match", False),
            "rows": rows,
            "sandbox_not_execution": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

    if mode == "markdown":
        print("# Phase160 Sandbox Board")
        print()
        print(f"| Example | Category | Safe | Invalid | Quarantine | Exec | Expectations |")
        print(f"|---------|----------|------|---------|------------|------|-------------|")
        for r in rows:
            cat = "trade-like" if r["is_trade_like"] else ("valid" if r["is_valid_example"] else "invalid")
            exp = "match" if r["expectations_match"] else ("fail" if r["expectations_match"] is False else "N/A")
            print(f"| {r['example_name']} | {cat} | {r['safe_count']} | {r['invalid_count']} | {r['quarantine_count']} | {r['execution_count']} | {exp} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
