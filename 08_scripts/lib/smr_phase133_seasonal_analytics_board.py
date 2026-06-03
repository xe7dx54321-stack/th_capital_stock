import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase133_financial_trend_panel_builder import build_financial_trend_panel
from smr_phase133_valuation_trend_panel_builder import build_valuation_trend_panel
from smr_phase133_cross_market_comparison_builder import build_cross_market_comparison
def build_seasonal_analytics_board():
 panels={"financial_trend":build_financial_trend_panel()["phase133_financial_trend_panel_builder"]["panel"],"valuation_trend":build_valuation_trend_panel()["phase133_valuation_trend_panel_builder"]["panel"],"cross_market":build_cross_market_comparison()["phase133_cross_market_comparison_builder"]["comparison"]}
 return {"phase133_seasonal_analytics_board":{"tickers_total":8,"panels":panels,"first_seasonal_snapshot":True,"not_trade_board":True,"mock_used":False,"fixture_used":False}}
