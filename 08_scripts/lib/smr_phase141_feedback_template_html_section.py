def build_feedback_template_html_section():
    html = '<div class="info-grid">'
    html += '<div class="info-card"><h4>Deep Dive Request</h4><p>Ticker: ___ | Thesis scope: ___ | Priority: high/medium/low</p></div>'
    html += '<div class="info-card"><h4>Evidence Challenge</h4><p>Ticker: ___ | Claim: ___ | Counter-evidence: ___</p></div>'
    html += '<div class="info-card"><h4>Source Upgrade Request</h4><p>Ticker: ___ | Current source: ___ | Desired source: ___</p></div>'
    html += '<div class="info-card"><h4>Runbook Feedback</h4><p>Module: ___ | Issue: ___ | Suggested fix: ___</p></div>'
    html += '</div>'
    return {"phase141_feedback_template_html_section": {"html": html, "templates": 4, "not_trade": True, "mock_used": False, "fixture_used": False}}
