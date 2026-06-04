import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase165_config import load_phase165_config
    from smr_phase165_guard import build_readiness_guard
    from smr_phase165_quality_gate import build_quality_gate
    from smr_phase165_cannot_conclude_guard import build_cannot_conclude_guard
    config = load_phase165_config()
    output = {"phase165_dashboard":{"phase":"phase165","strategy":config.get("strategy",""),"research_only":True,"agent_simulation_only":True,"llm_api_enabled":False,"guard":build_readiness_guard()["phase165_readiness_guard"]["status"],"quality_gate":build_quality_gate()["phase165_quality_gate"]["status"],"cannot_conclude_guard":build_cannot_conclude_guard()["phase165_cannot_conclude_guard"]["status"],"violations":0,"safety":{"activation_execution_allowed":False,"target_price_output_allowed":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0}}}
    if mode=="markdown":
        d=output["phase165_dashboard"]
        print("# Phase165 Dashboard")
        print(f"| Guard | {d['guard']} |");print(f"| Quality Gate | {d['quality_gate']} |");print(f"| CC Guard | {d['cannot_conclude_guard']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__=="__main__": main("markdown" if "--markdown" in sys.argv else "json")
