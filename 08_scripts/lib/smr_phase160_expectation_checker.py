def check_expectations(example, validation_result):
    v = validation_result.get("phase160_sandbox_validation", {})
    expected = {
        "safe": example.get("expected_safe_count", 0),
        "invalid": example.get("expected_invalid_count", 0),
        "quarantine": example.get("expected_quarantine_count", 0),
        "preview": example.get("expected_preview_count", 0),
        "execution": example.get("expected_execution_count", 0)
    }
    actual = {
        "safe": v.get("safe_count", 0),
        "invalid": v.get("invalid_count", 0),
        "quarantine": v.get("quarantine_count", 0),
        "preview": v.get("preview_count", 0),
        "execution": v.get("execution_count", 0)
    }
    matches = all(expected[k] == actual[k] for k in expected)

    return {
        "phase160_expectation_checker": {
            "example_id": example.get("example_id", ""),
            "example_name": example.get("example_name", ""),
            "expectations_match": matches,
            "expected": expected,
            "actual": actual,
            "mismatches": [k for k in expected if expected[k] != actual[k]],
            "mock_used": False,
            "fixture_used": False
        }
    }

def check_all_expectations(examples, validation_results):
    results = []
    for ex, vr in zip(examples, validation_results):
        results.append(check_expectations(ex, vr))

    all_match = all(r["phase160_expectation_checker"]["expectations_match"] for r in results)

    return {
        "phase160_expectation_checker_aggregate": {
            "total_checked": len(results),
            "all_expectations_match": all_match,
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
