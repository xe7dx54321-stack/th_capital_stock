def build_owner_approval_checklist(candidate):
    return {"packet_type": "owner_approval_checklist", "ticker": candidate["ticker"],
        "checklist_items": [
            {"item": "thesis_reviewed", "status": "pending", "requires": "Read thesis seed and confirm or reject"},
            {"item": "source_verified", "status": "pending", "requires": "Confirm SEC EDGAR route"},
            {"item": "financials_checked", "status": "pending", "requires": "Confirm financial route and metrics"},
            {"item": "valuation_checked", "status": "pending", "requires": "Confirm valuation approach (derived label only)"},
            {"item": "risk_assessed", "status": "pending", "requires": "Review known risks"},
            {"item": "ready_for_watchlist", "status": "pending", "requires": "Final decision: approve or hold"},
        ],
        "all_items_pending": True, "requires_owner_sign_off": True,
        "owner_approval_not_equal_to_trade_approval": True,
        "mock_used": False, "fixture_used": False}
