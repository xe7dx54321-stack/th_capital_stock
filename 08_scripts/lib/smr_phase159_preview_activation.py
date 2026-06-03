def build_preview_activation(safe_manifest):
    previews = []
    for d in safe_manifest.get("safe_decisions",[]):
        if d["decision"] == "approve_research_activation":
            previews.append({"ticker":d["ticker"],"preview":"research activation plan prepared","auto_execute":False,"requires_owner_final_sign_off":True})
    return {"phase159_preview_activation":{"previews":len(previews),"results":previews,"preview_is_not_real_activation":True,"execution_blocked":True,"mock_used":False,"fixture_used":False}}
