import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase140_hardening_brief import build_hardening_brief_md
def main():
 md=build_hardening_brief_md()
 if "--markdown" in sys.argv or "--json" in sys.argv:
  import json; print(json.dumps({"phase140_hardening_brief":{"markdown":md,"mock_used":False,"fixture_used":False}},ensure_ascii=False))
 else: print(md)
if __name__=="__main__":main()
