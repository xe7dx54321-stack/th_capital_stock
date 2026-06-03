import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase133_seasonal_analytics_board import build_seasonal_analytics_board
from smr_phase133_seasonal_analytics_brief import build_seasonal_analytics_brief_md
def build_seasonal_dashboard_export():
 board=build_seasonal_analytics_board()["phase133_seasonal_analytics_board"]
 brief=build_seasonal_analytics_brief_md()
 return {"phase133_seasonal_dashboard_exporter":{"format_available":["json","markdown"],"board":board,"brief_preview":brief[:200]+"...","export_ready":True,"mock_used":False,"fixture_used":False}}
