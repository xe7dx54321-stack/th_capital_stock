import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase133_seasonal_analytics_brief import build_seasonal_analytics_brief_md
def main():
 if "--markdown" in sys.argv: print(build_seasonal_analytics_brief_md())
 elif "--json" in sys.argv: print(json.dumps({"phase133_seasonal_brief":{"markdown_preview":build_seasonal_analytics_brief_md()[:200]+"...","mock_used":False,"fixture_used":False}},ensure_ascii=False,indent=2))
 else: print(build_seasonal_analytics_brief_md())
if __name__=="__main__":main()
