import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase134_console_memory import build_console_memory
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 r=build_console_memory()
 out={"phase134_console_memory_writer":{"mode":mode,"records_written":r["phase134_console_memory"]["records_written"],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
