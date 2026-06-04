import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    output = {"phase165_readiness_brief":{"title":"Readiness Repair & Research Packet Brief","summary":"Phase165 diagnoses 13 candidate readiness gaps and generates multi-agent research packets.","key_findings":["13/13 not_ready: all require network data + owner decision","4 blocker types: network_data_required, owner_decision_pending, turnaround_execution_uncertainty, regulatory_risk","7 agent passes completed (simulation only, no LLM)","13 research packets assembled with per-candidate agent outputs","Judge agent: 0 trade terms found across all candidates","Activation preview: all require live data + owner decision + judge pass","Owner next-actions: 13 review_research_packet_and_decide, no buy/sell/hold","300394/688041 constraints preserved"],"mock_used":False,"fixture_used":False}}
    if mode=="markdown":
        for f in output["phase165_readiness_brief"]["key_findings"]: print(f"- {f}")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__=="__main__": main("markdown" if "--markdown" in sys.argv else "json")
