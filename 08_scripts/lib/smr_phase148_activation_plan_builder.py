def build_activation_plans():
    plans = []
    for tkr in ["TSM", "ASML", "SNOW", "MU", "AMD"]:
        plans.append({
            "ticker": tkr,
            "activation_steps": [
                "1. Verify ticker identity normalization",
                "2. Confirm primary data source (SEC EDGAR)",
                "3. Load financial statements (revenue, gross_profit, net_income, OCF)",
                "4. Normalize currency and period (USD, FY/Q/TTM)",
                "5. Build initial valuation framework",
                "6. Draft investment thesis statement",
                "7. Establish evidence chain baseline",
                "8. Generate HTML detail placeholder page",
                "9. Create agent task queue entries",
                "10. Obtain manual owner approval before watchlist addition",
            ],
            "blockers": [],
            "requires_owner_approval": True,
            "approval_checklist": ["thesis_reviewed", "source_verified", "valuation_checked", "risk_assessed", "ready_for_watchlist"],
            "status": "planning",
        })
    return {"phase148_activation_plans": {"plans": len(plans), "activation_plans": plans, "mock_used": False, "fixture_used": False}}
