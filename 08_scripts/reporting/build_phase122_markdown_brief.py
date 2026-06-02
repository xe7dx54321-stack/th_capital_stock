import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase122_markdown_brief import build_markdown_brief
def main():
 r=build_markdown_brief()
 if "--markdown" in sys.argv: print(r["phase122_markdown_brief"]["markdown"])
 elif "--json" in sys.argv: print(json.dumps({"phase122_markdown_brief":{"generated":r["phase122_markdown_brief"]["generated"],"sections":r["phase122_markdown_brief"]["sections"],"lines":r["phase122_markdown_brief"]["lines"]}},ensure_ascii=False,indent=2))
 else: print(r["phase122_markdown_brief"]["markdown"])
if __name__=="__main__":main()
