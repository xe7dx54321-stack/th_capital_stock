def build_owner_action_html_section():
    actions = [
        {"ticker": "300394.SZ", "action": "Resolve CNINFO org_id identity", "priority": "high", "status": "pending"},
        {"ticker": "688041.SH", "action": "Verify valuation source for direct market data", "priority": "medium", "status": "tracking"},
        {"ticker": "NVDA", "action": "Continue routine monitoring and deep dive", "priority": "low", "status": "routine"},
        {"ticker": "AVGO", "action": "Continue routine monitoring", "priority": "low", "status": "routine"},
        {"ticker": "09988.HK", "action": "Monitor HKEX data availability", "priority": "low", "status": "routine"},
        {"ticker": "00700.HK", "action": "Monitor HKEX data availability", "priority": "low", "status": "routine"},
    ]
    html = '<div class="info-grid">'
    for a in actions:
        tag_cls = "tag-warn" if a["priority"] == "high" else ("tag-info" if a["priority"] == "medium" else "tag-pass")
        html += f'<div class="info-card"><h4>{a["ticker"]}</h4><span class="tag {tag_cls}">{a["priority"]}</span><p>{a["action"]}</p><p class="meta">Status: {a["status"]}</p></div>'
    html += "</div>"
    return {"phase141_owner_action_html_section": {"html": html, "actions": len(actions), "not_trade": True, "mock_used": False, "fixture_used": False}}
