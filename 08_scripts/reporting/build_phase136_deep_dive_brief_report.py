import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase136_deep_dive_brief_builder import build_deep_dive_brief_md
def main():
 md=build_deep_dive_brief_md()
 if "--markdown" in sys.argv or "--json" in sys.argv:
  import json; print(json.dumps({"phase136_deep_dive_brief":{"markdown":md,"mock_used":False,"fixture_used":False}},ensure_ascii=False))
 else: print(md)
if __name__=="__main__":main()
