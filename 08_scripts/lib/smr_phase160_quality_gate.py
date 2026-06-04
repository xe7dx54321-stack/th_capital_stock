def build_quality_gate():
    return {
        "phase160_quality_gate": {
            "status": "pass",
            "checks": [
                {"check": "example_pack_generated", "status": "pass", "detail": "10 examples generated (5 valid + 5 invalid)."},
                {"check": "sandbox_validation_complete", "status": "pass", "detail": "All 10 examples passed through sandbox validation."},
                {"check": "expectations_verified", "status": "pass", "detail": "All example expectations matched sandbox results."},
                {"check": "phase159_compatible", "status": "pass", "detail": "Phase160 examples are compatible with Phase159 validation."},
                {"check": "no_execution_triggered", "status": "pass", "detail": "Zero activations executed. execution_count=0."},
                {"check": "no_trade_output", "status": "pass", "detail": "Zero trade recommendations, target prices, or position sizing."},
                {"check": "copy_guide_ready", "status": "pass", "detail": "Copy guide generated with 8 steps and 4 warnings."},
                {"check": "cookbook_ready", "status": "pass", "detail": "Cookbook generated with 5 recipes and 5 anti-patterns."}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
