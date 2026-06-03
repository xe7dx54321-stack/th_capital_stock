def build_artifact_link_index():
 links=[
  {"artifact":"Phase132 Dashboard","path":"08_scripts/reporting/build_phase132_dashboard.py","format":"json/markdown","category":"coverage"},
  {"artifact":"Phase133 Dashboard","path":"08_scripts/reporting/build_phase133_dashboard.py","format":"json","category":"seasonal"},
  {"artifact":"Phase133 Seasonal Brief","path":"08_scripts/reporting/build_phase133_seasonal_analytics_brief_report.py","format":"markdown","category":"seasonal"},
  {"artifact":"Phase134 Console JSON","path":"08_scripts/reporting/build_phase134_console_json_export.py","format":"json","category":"console"},
  {"artifact":"Phase134 Console Report","path":"08_scripts/reporting/build_phase134_console_markdown_report.py","format":"markdown","category":"console"},
  {"artifact":"Phase134 Console HTML","path":"08_scripts/reporting/build_phase134_console_html_skeleton.py","format":"html","category":"console"},
  {"artifact":"Phase134 Dashboard","path":"08_scripts/reporting/build_phase134_dashboard.py","format":"json","category":"console"},
  {"artifact":"Phase122 Daily Brief","path":"08_scripts/reporting/build_phase122_daily_brief_report.py","format":"markdown","category":"daily"}
 ]
 return {"phase134_artifact_link_index":{"links":links,"total":len(links),"all_paths_relative":True,"mock_used":False,"fixture_used":False}}
