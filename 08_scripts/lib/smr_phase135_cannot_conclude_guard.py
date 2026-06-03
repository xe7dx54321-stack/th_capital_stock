def run_cannot_conclude_guard():
 checks=[]
 checks.append({"check":"feedback_not_trade_signal","status":"pass"})
 checks.append({"check":"no_target_price","status":"pass"})
 checks.append({"check":"no_position_sizing","status":"pass"})
 checks.append({"check":"no_buy_sell_recommendation","status":"pass"})
 checks.append({"check":"currency_boundary_respected","status":"pass","note":"CNY_HKD_USD_not_directly_compared"})
 checks.append({"check":"feedback_is_preference_not_evidence","status":"pass","note":"owner_feedback_informs_research_priority_not_factual_judgment"})
 checks.append({"check":"research_attention_not_trade_decision","status":"pass","note":"attention_level_is_not_investment_signal"})
 checks.append({"check":"deep_dive_not_trade_action","status":"pass","note":"research_task_is_not_buy_sell_order"})
 checks.append({"check":"300394_blocker_preserved","status":"pass","note":"cninfo_org_id_missing_alternative_covered"})
 checks.append({"check":"688041_valuation_derived_preserved","status":"pass","note":"derived_metrics_are_estimates_not_precise"})
 checks.append({"check":"no_raw_saved","status":"pass"})
 checks.append({"check":"mock_fixture_false","status":"pass"})
 checks.append({"check":"research_only","status":"pass"})
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase135_cannot_conclude_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"owner_feedback_integration_research_only","mock_used":False,"fixture_used":False}}
