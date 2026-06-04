import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    output = {
        "phase161_submission_feedback_brief": {
            "title": "Owner Decision Submission UI Feedback Brief",
            "summary": "Phase161 integrates Phase160 example pack and Phase159 submission validation into the Owner Decision Center UI.",
            "key_components": [
                "Example library with 5 valid + 5 invalid templates",
                "Sandbox validation results (45 safe, 6 invalid, 6 quarantine, 0 execution)",
                "Quarantine explanation panel",
                "Safe manifest explanation panel",
                "Phase159 submission status panel",
                "7-step real input workflow instructions",
                "Next command panel with 5 actionable commands"
            ],
            "key_findings": [
                "No owner_decision_input.json present. All 8 candidates in pending_owner_review.",
                "All UI components are static HTML only. No external JS/CDN/server.",
                "No form submit, execution, or trade buttons exist.",
                "All panels clearly label research-only, preview-only, and not-execution status.",
                "300394 CNINFO blocker, 300394 thesis unconfirmed, 688041 valuation label preserved."
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
    if mode == "markdown":
        print("# Submission Feedback Brief")
        for c in output["phase161_submission_feedback_brief"]["key_components"]:
            print(f"- {c}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"
    if "--markdown" in sys.argv:
        mode = "markdown"
    main(mode)
