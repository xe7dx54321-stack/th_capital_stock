import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase136_feedback_memory_integration_update import build_feedback_memory_integration_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 r=build_feedback_memory_integration_update()
 out={"phase136_deep_dive_workflow_memory_writer":{"mode":mode,"records_written":r["phase136_feedback_memory_integration_update"]["total"],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
