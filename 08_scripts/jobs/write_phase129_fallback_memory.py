import json,sys,os,datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase129_fallback_memory import build_fallback_memory
def main():
 m=build_fallback_memory(); now=datetime.datetime.now().isoformat(); rec={"run":"phase129_fallback","timestamp":now,"memory":m}
 if "--dry-run" in sys.argv: print(json.dumps({"mode":"dry_run","would_write":1,"path":m["phase129_fallback_memory"]["path"],"gitignored":m["phase129_fallback_memory"]["gitignored"]},ensure_ascii=False,indent=2))
 elif "--execute" in sys.argv:
  p=os.path.join(os.path.dirname(__file__),"..","..",m["phase129_fallback_memory"]["path"]); os.makedirs(os.path.dirname(p),exist_ok=True)
  with open(p,"a",encoding="utf-8") as fh: fh.write(json.dumps(rec,ensure_ascii=False)+"\n")
  print(json.dumps({"mode":"execute","records_written":1,"path":m["phase129_fallback_memory"]["path"],"gitignored":m["phase129_fallback_memory"]["gitignored"],"mock_used":False,"fixture_used":False},ensure_ascii=False,indent=2))
 else: print(json.dumps(rec,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
