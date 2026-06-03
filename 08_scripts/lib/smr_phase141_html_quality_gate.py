def run_html_quality_gate(html_content):
    checks = {}
    checks["has_doctype"] = "<!DOCTYPE html>" in html_content
    checks["has_meta_charset"] = "charset" in html_content.lower()
    checks["has_title"] = "<title>" in html_content
    checks["no_external_script"] = 'src="http' not in html_content and "src='http" not in html_content
    checks["no_cdn_link"] = "cdn." not in html_content.lower() and "unpkg" not in html_content.lower()
    checks["no_inline_event_handler"] = "onclick=" not in html_content and "onerror=" not in html_content
    checks["has_footer_disclaimer"] = "Research-only" in html_content or "No trade recommendations" in html_content
    checks["has_all_sections"] = all(s in html_content for s in ["ticker-cards", "thesis-library", "evidence-sources", "daily-delivery", "owner-actions", "gap-risk", "feedback-template", "artifact-links"])
    checks["has_navigation"] = "nav-bar" in html_content or "navigation" in html_content
    checks["has_status_bar"] = "status-bar" in html_content or "system-status" in html_content
    all_pass = all(checks.values())
    return {
        "phase141_html_quality_gate": {
            "overall_status": "pass" if all_pass else "fail",
            "checks": checks,
            "all_pass": all_pass,
            "failed_checks": [k for k, v in checks.items() if not v],
            "static_html_only": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
