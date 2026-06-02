def build_ticker_cards():
 cards=[
  {"ticker":"NVDA","market":"US","signal":"strengthened","top_metric":"revenue","catalyst":"confirmed_inflection","sources":8,"source_risk":"moderate","currency":"USD","cannot_conclude":["customer_share","order_volume","specific_growth_rate"]},
  {"ticker":"AVGO","market":"US","signal":"unchanged","top_metric":"revenue","sources":8,"source_risk":"moderate","currency":"USD","cannot_conclude":["customer_concentration","chip_allocation"]},
  {"ticker":"09988.HK","market":"HK","signal":"strengthened","top_metric":"revenue","sources":6,"source_risk":"reduced","currency":"HKD","cannot_conclude":["cloud_market_share","ecommerce_take_rate"]},
  {"ticker":"00700.HK","market":"HK","signal":"unchanged","top_metric":"net_profit","sources":6,"source_risk":"reduced","currency":"HKD","cannot_conclude":["game_revenue_split","ad_revenue_growth"]},
  {"ticker":"300308.SZ","market":"CN_A","signal":"unchanged","top_metric":"revenue","sources":2,"source_risk":"moderate","currency":"CNY","cannot_conclude":["optical_module_shipment","customer_concentration"]},
  {"ticker":"688041.SH","market":"CN_A","signal":"unchanged","top_metric":"revenue","sources":2,"source_risk":"moderate","currency":"CNY","cannot_conclude":["DCU_shipment_volume","pricing_power"],"partial":"valuation"},
  {"ticker":"002230.SZ","market":"CN_A","signal":"unchanged","top_metric":"revenue","sources":2,"source_risk":"moderate","currency":"CNY","cannot_conclude":["edu_IT_budget","AI_model_monetization"]},
 ]
 return {"phase122_ticker_cards":{"total":len(cards),"covered":7,"cards":cards,"research_only":True,"mock_used":False,"fixture_used":False}}
