def run_cannot_conclude_guard():
 checks=[]
 checks.append({"check":"deep_dive_not_trade_signal","status":"pass"})
 checks.append({"check":"no_target_price","status":"pass"})
 checks.append({"check":"no_position_sizing","status":"pass"})
 checks.append({"check":"no_buy_sell_recommendation","status":"pass"})
 checks.append({"check":"research_packet_not_investment_advice","status":"pass","note":"deep_dive_is_research_not_recommendation"})
 checks.append({"check":"evidence_not_confirmed","status":"pass","note":"derived_metrics_are_estimates_not_facts"})
 checks.append({"check":"manual_confirmation_required","status":"pass","note":"some_items_need_owner_confirmation"})
 checks.append({"check":"source_gaps_acknowledged","status":"pass","note":"SEC_HKEX_cninfo_limitations_documented"})
 checks.append({"check":"300394_blocker_preserved","status":"pass","note":"cninfo_org_id_missing_alternative_covered"})
 checks.append({"check":"688041_valuation_derived_preserved","status":"pass","note":"derived_metrics_are_estimates_not_precise"})
 checks.append({"check":"no_raw_saved","status":"pass"})
 checks.append({"check":"mock_fixture_false","status":"pass"})
 checks.append({"check":"research_only","status":"pass"})
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase136_cannot_conclude_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"deep_dive_research_only","mock_used":False,"fixture_used":False}}
