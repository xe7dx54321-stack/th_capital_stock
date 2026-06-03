def build_opportunity_catalyst_center():
 catalysts=[
  {"ticker":"NVDA","market":"US","catalyst":"AI_capex_cycle_quarterly_earnings","type":"earnings_driver","status":"active_tracking","next_check":"next_quarterly_report"},
  {"ticker":"688041.SH","market":"CN_A","catalyst":"domestic_semiconductor_substitution_policy","type":"policy_driver","status":"active_tracking","next_check":"policy_update_cycle"},
  {"ticker":"09988.HK","market":"HK","catalyst":"cloud_AI_revenue_acceleration","type":"segment_driver","status":"active_tracking","next_check":"next_quarterly_report"},
  {"ticker":"AVGO","market":"US","catalyst":"AI_networking_ASIC_demand","type":"product_cycle","status":"active_tracking","next_check":"next_quarterly_report"},
  {"ticker":"00700.HK","market":"HK","catalyst":"gaming_cycle_and_ad_recovery","type":"segment_driver","status":"active_tracking","next_check":"next_quarterly_report"}
 ]
 return {"phase134_opportunity_catalyst_center":{"catalysts":catalysts,"total":len(catalysts),"not_trade_signal":True,"cannot_conclude":["buy_signal","sell_signal","target_price","position_sizing"],"mock_used":False,"fixture_used":False}}
