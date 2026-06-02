def build_feedback_classifier():
 types=["opportunity_quality","brief_quality","evidence_quality","source_quality","risk_alert","gap_alert","action_feedback","ticker_priority","research_direction","noise_reduction","report_format","owner_note"]
 return {"phase123_feedback_classifier":{"version":"v1","feedback_types":12,"types":types,"invalid_types":["buy_recommendation","sell_recommendation","trade_signal","price_prediction","position_allocation"],"trade_like_rejected":True,"mock_used":False,"fixture_used":False}}
