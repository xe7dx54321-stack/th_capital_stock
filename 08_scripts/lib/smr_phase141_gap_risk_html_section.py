def build_gap_risk_html_section():
    gaps = [
        {"ticker": "300394.SZ", "gap": "CNINFO org_id missing blocks full structured financial coverage", "severity": "high", "mitigation": "eastmoney alternative provides partial data"},
        {"ticker": "688041.SH", "gap": "Valuation metrics are derived, not direct market-sourced", "severity": "medium", "mitigation": "Labeled as derived; tracked for source upgrade"},
        {"ticker": "NVDA", "gap": "SEC EDGAR direct access limitation", "severity": "low", "mitigation": "Public filings and earnings summaries used"},
        {"ticker": "HK", "gap": "HKEX official source direct access limitation", "severity": "low", "mitigation": "Alternative financial data providers used"},
        {"ticker": "300308.SZ", "gap": "Optical demand data is contextual, not direct order-book", "severity": "medium", "mitigation": "Contextual evidence from industry data used"},
    ]
    html = '<div class="info-grid">'
    for g in gaps:
        tag_cls = "tag-warn" if g["severity"] == "high" else ("tag-info" if g["severity"] == "medium" else "tag-pass")
        html += f'<div class="info-card"><h4>{g["ticker"]}</h4><span class="tag {tag_cls}">{g["severity"]}</span><p><strong>Gap:</strong> {g["gap"]}</p><p><strong>Mitigation:</strong> {g["mitigation"]}</p></div>'
    html += "</div>"
    return {"phase141_gap_risk_html_section": {"html": html, "gaps": len(gaps), "not_trade": True, "mock_used": False, "fixture_used": False}}
