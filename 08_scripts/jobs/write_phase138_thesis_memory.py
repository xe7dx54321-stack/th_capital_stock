import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase138_thesis_memory_writer import build_thesis_memory
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 r=build_thesis_memory()
 out={"phase138_thesis_memory_writer_job":{"mode":mode,"records_written":r["phase138_thesis_memory_writer"]["total"],"path_ignored":True,"mock_used":False,"fixture_used":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
