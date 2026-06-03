def run_detail_quality_gate(html_pages):
    checks = {}
    checks["all_8_pages_generated"] = len(html_pages) == 8
    checks["all_have_doctype"] = all("<!DOCTYPE html>" in p for p in html_pages.values())
    checks["all_have_title"] = all("<title>" in p for p in html_pages.values())
    checks["no_external_script"] = all('src="http' not in p for p in html_pages.values())
    checks["no_cdn"] = all("cdn." not in p.lower() for p in html_pages.values())
    checks["all_have_footer"] = all("Research-only" in p for p in html_pages.values())
    checks["all_have_back_link"] = all("Research Console" in p for p in html_pages.values())
    checks["all_have_timeline"] = all("timeline" in p for p in html_pages.values())
    checks["all_have_evidence"] = all("evidence" in p.lower() for p in html_pages.values())
    all_pass = all(checks.values())
    return {"phase142_detail_quality_gate": {"overall_status": "pass" if all_pass else "fail", "checks": checks, "all_pass": all_pass, "failed_checks": [k for k, v in checks.items() if not v], "mock_used": False, "fixture_used": False}}
