def run_phase143_quality_gate(integrity_result):
    ic = integrity_result.get("phase143_link_integrity_check", {})
    checks = {
        "integrity_pass": ic.get("overall_status") == "pass",
        "all_files_exist": ic.get("files_fail", 1) == 0,
        "all_required_sections": all(r.get("status") == "pass" for r in ic.get("results", [{}])),
    }
    all_pass = all(checks.values())
    return {"phase143_quality_gate": {"overall_status": "pass" if all_pass else "fail", "checks": checks, "all_pass": all_pass, "failed_checks": [k for k, v in checks.items() if not v], "mock_used": False, "fixture_used": False}}
