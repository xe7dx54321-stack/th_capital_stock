def build_decision_ui_data_model(candidates):
    model = [{"ticker":c["ticker"],"name":c["name"],"decision":c["decision"],"admission_score":c.get("admission_score",""),"market":c.get("market",""),"card_sections":["ticker_identity","admission_summary","decision_options","simulation_preview","safety_notes"]} for c in candidates]
    return {"phase158_ui_data_model":{"candidates":len(model),"cards":model,"static_html_only":True,"dynamic_js_disabled":True,"mock_used":False,"fixture_used":False}}
