def build_brief_layout_feedback_adapter():
 adjustments=[
  {"from_feedback":"FB-DB-001","layout_change":"expand_seasonal_context","section":"boss_summary","before":"minimal_seasonal_context","after":"include_seasonal_highlights","reason":"Owner requested more seasonal context in brief"},
  {"from_feedback":"FB-SI-001","layout_change":"preserve_seasonal_insight_section","section":"analyst_detail","before":"seasonal_mentioned","after":"seasonal_highlighted","reason":"Owner finds seasonal insight helpful"}
 ]
 return {"phase135_brief_layout_feedback_adapter":{"adjustments":adjustments,"total_adjusted":len(adjustments),"not_trade_signal":True,"mock_used":False,"fixture_used":False}}
