def run_feedback_validator():
 all_feedbacks=[]
 # Collect from all intakes
 from smr_phase135_ticker_card_feedback_intake import build_ticker_card_feedback_intake
 from smr_phase135_owner_action_feedback_intake import build_owner_action_feedback_intake
 from smr_phase135_daily_brief_feedback_intake import build_daily_brief_feedback_intake
 from smr_phase135_source_signal_feedback_intake import build_source_signal_feedback_intake
 from smr_phase135_gap_risk_feedback_intake import build_gap_risk_feedback_intake
 from smr_phase135_seasonal_insight_feedback_intake import build_seasonal_insight_feedback_intake
 all_feedbacks.extend(build_ticker_card_feedback_intake()["phase135_ticker_card_feedback_intake"]["feedbacks"])
 all_feedbacks.extend(build_owner_action_feedback_intake()["phase135_owner_action_feedback_intake"]["feedbacks"])
 all_feedbacks.extend(build_daily_brief_feedback_intake()["phase135_daily_brief_feedback_intake"]["feedbacks"])
 all_feedbacks.extend(build_source_signal_feedback_intake()["phase135_source_signal_feedback_intake"]["feedbacks"])
 all_feedbacks.extend(build_gap_risk_feedback_intake()["phase135_gap_risk_feedback_intake"]["feedbacks"])
 all_feedbacks.extend(build_seasonal_insight_feedback_intake()["phase135_seasonal_insight_feedback_intake"]["feedbacks"])
 forbidden=["buy","sell","short","add_position","reduce_position","target_price","position_size","profit","loss","return","alpha","order","trade"]
 valid=[];invalid=[];rejected_trade=[]
 for fb in all_feedbacks:
  if not fb.get("research_only") or not fb.get("not_trade_feedback"):
   rejected_trade.append(fb)
  elif any(w in str(fb.get("owner_comment","")).lower() for w in forbidden):
   rejected_trade.append(fb)
  elif fb.get("feedback_type") not in ["ticker_card_useful","ticker_card_not_useful","raise_research_attention","lower_research_attention","request_deep_dive","brief_too_long","brief_too_shallow","brief_priority_unclear","source_noisy","signal_helpful","gap_priority_high","gap_priority_low"]:
   invalid.append(fb)
  else:
   valid.append(fb)
 return {"phase135_feedback_validator":{"valid_feedback_count":len(valid),"invalid_feedback_count":len(invalid),"rejected_trade_like_feedback":len(rejected_trade),"all_feedbacks_checked":len(all_feedbacks),"valid_feedbacks":valid,"invalid_feedbacks":invalid,"rejected_feedbacks":rejected_trade,"mock_used":False,"fixture_used":False}}
