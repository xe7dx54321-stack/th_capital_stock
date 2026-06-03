def build_artifact_link_html_section():
    links = [
        {"label": "Phase140 Hardening Report", "path": "09_runbooks/reports/phase140_hardening_report.md", "type": "report"},
        {"label": "Phase139 Daily Delivery", "path": "09_runbooks/reports/phase139_daily_delivery.md", "type": "delivery"},
        {"label": "Phase138 Thesis Library", "path": "09_runbooks/reports/phase138_thesis_library.md", "type": "thesis"},
        {"label": "Runbook Index", "path": "09_runbooks/smr-research-upgrade-progress.md", "type": "index"},
        {"label": "Config: HTML Dashboard", "path": "config/phase141_html_dashboard.json", "type": "config"},
    ]
    html = '<div class="info-grid">'
    for lk in links:
        html += f'<div class="info-card"><h4>{lk["label"]}</h4><p class="meta">Type: {lk["type"]}</p><p><code>{lk["path"]}</code></p></div>'
    html += '</div>'
    return {"phase141_artifact_link_html_section": {"html": html, "links": len(links), "not_trade": True, "mock_used": False, "fixture_used": False}}
