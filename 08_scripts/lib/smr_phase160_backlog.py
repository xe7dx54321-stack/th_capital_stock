def build_backlog_update():
    return {
        "phase160_backlog": {
            "phase": "phase160",
            "status": "completed",
            "summary": "Owner Decision Example Pack & Safe Input Sandbox v1",
            "deliverables": [
                "10 example templates (5 valid + 5 invalid)",
                "Sandbox input writer and validation runner",
                "Expectation checker for all 10 examples",
                "Phase159 compatibility verification",
                "Copy guide with 8 steps",
                "Owner decision cookbook with 5 recipes",
                "Sandbox board and brief",
                "Research-only sandbox guard",
                "Quality gate and cannot-conclude guard"
            ],
            "next_phase_recommendation": "Phase 161: If owner wants to proceed with candidate activation, run Phase159 with real owner_decision_input.json. Otherwise continue with research pipeline enhancements.",
            "mock_used": False,
            "fixture_used": False
        }
    }
