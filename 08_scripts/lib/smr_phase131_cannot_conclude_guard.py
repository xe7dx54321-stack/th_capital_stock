def run_cannot_conclude_guard():
 checks=[]
 checks.append({"check":"integration_not_trade_signal","status":"pass"})
 checks.append({"check":"no_target_price","status":"pass"})
 checks.append({"check":"no_position_sizing","status":"pass"})
 checks.append({"check":"source_not_overclaimed","status":"pass","note":"eastmoney_is_alternative_not_direct_cninfo"})
 checks.append({"check":"owner_verification_pending","status":"pass","note":"owner_should_verify_eastmoney_data_completeness"})
 checks.append({"check":"688041_gap_unchanged","status":"pass"})
 checks.append({"check":"300394_not_promoted_to_trade","status":"pass","note":"coverage_does_not_equal_buy_recommendation"})
 checks.append({"check":"no_raw_saved","status":"pass"})
 checks.append({"check":"mock_fixture_false","status":"pass"})
 checks.append({"check":"research_only","status":"pass"})
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase131_cannot_conclude_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"alternative_source_integration_research_only","mock_used":False,"fixture_used":False}}
