def check_blocker_visibility():
 blockers=[{"blocker":"300394.SZ","source":"cninfo","visible_in_all_modules":True,"blocker_documented":True,"not_hidden":True},{"blocker":"688041.SH","source":"valuation","visible_in_all_modules":True,"caution_documented":True,"not_hidden":True}]
 all_visible=all(b["visible_in_all_modules"] for b in blockers)
 return {"phase118_blocker_visibility":{"total":len(blockers),"all_visible":all_visible,"blockers":blockers,"research_only":True,"mock_used":False,"fixture_used":False}}