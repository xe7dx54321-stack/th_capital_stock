def build_feedback_html_section():
    L = chr(60); R = chr(62)
    html = L+"section id=feedback-forms"+R
    html += L+"h2"+R+"Owner Feedback Forms"+L+"/h2"+R
    html += L+"div class=info-grid"+R

    forms = [
        {"id": "general", "name": "General Research Feedback", "desc": "Submit general observations, concerns, or ideas about any ticker or the research system."},
        {"id": "source", "name": "Source Limitation Confirmation", "desc": "Acknowledge or dispute current source limitations for specific tickers."},
        {"id": "thesis", "name": "Thesis Review", "desc": "Review and update thesis status, confidence level, and new evidence."},
        {"id": "deepdive", "name": "Deep Dive Follow-up", "desc": "Trigger a new deep dive investigation for a specific ticker or topic."},
        {"id": "checklist", "name": "Confirmation Checklist", "desc": "Per-ticker manual confirmation checklist for phase completion."},
    ]
    for form in forms:
        html += L+"div class=info-card"+R
        html += L+"h4"+R+form["name"]+L+"/h4"+R
        html += L+"p"+R+form["desc"]+L+"/p"+R
        html += L+"p class=meta"+R+"Template: feedback_"+form["id"]+".md / .json"+L+"/p"+R
        html += L+"/div"+R
    html += L+"/div"+R+L+"/section"+R
    return {"phase144_feedback_html_section": {"html": html, "forms": len(forms), "not_trade": True, "mock_used": False, "fixture_used": False}}
