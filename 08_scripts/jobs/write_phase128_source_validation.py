import json,sys,os,datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase128_validation_memory import build_validation_memory
def main():
 mem=build_validation_memory()
 now=datetime.datetime.now().isoformat()
 record={"run":"phase128_source_validation","timestamp":now,"memory":mem}
 dry="--dry-run" in sys.argv
 exe="--execute" in sys.argv
 if dry:
  print(json.dumps({"mode":"dry_run","would_write":1,"path":mem["phase128_validation_memory"]["path"],"gitignored":mem["phase128_validation_memory"]["gitignored"]},ensure_ascii=False,indent=2))
 elif exe:
  p=os.path.join(os.path.dirname(__file__),"..","..",mem["phase128_validation_memory"]["path"])
  os.makedirs(os.path.dirname(p),exist_ok=True)
  with open(p,"a",encoding="utf-8") as fh:
   fh.write(json.dumps(record,ensure_ascii=False)+"\n")
  print(json.dumps({"mode":"execute","records_written":1,"path":mem["phase128_validation_memory"]["path"],"gitignored":mem["phase128_validation_memory"]["gitignored"],"mock_used":False,"fixture_used":False},ensure_ascii=False,indent=2))
 else:
  print(json.dumps(record,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
