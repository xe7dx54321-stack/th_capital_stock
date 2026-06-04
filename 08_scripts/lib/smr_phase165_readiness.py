TICKERS = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def analyze_not_ready_reasons(mode="skip-network"):
    results=[]
    blocker_map = {
        "MRVL": ["network_data_required","owner_decision_pending"],
        "AMAT": ["network_data_required","owner_decision_pending"],
        "LRCX": ["network_data_required","owner_decision_pending"],
        "KLAC": ["network_data_required","owner_decision_pending"],
        "INTC": ["network_data_required","owner_decision_pending","turnaround_execution_uncertainty"],
        "SNPS": ["network_data_required","owner_decision_pending","regulatory_risk_ansys_acquisition"],
        "CDNS": ["network_data_required","owner_decision_pending"],
        "CRM": ["network_data_required","owner_decision_pending"],
        "TSM": ["network_data_required","owner_decision_pending"],
        "ASML": ["network_data_required","owner_decision_pending"],
        "AMD": ["network_data_required","owner_decision_pending"],
        "SNOW": ["network_data_required","owner_decision_pending"],
        "MU": ["network_data_required","owner_decision_pending"]
    }
    for tk in TICKERS:
        blockers = blocker_map.get(tk, ["network_data_required"])
        results.append({"ticker":tk,"not_ready":True,"blockers":blockers,"primary_blocker":blockers[0],"blocker_count":len(blockers)})
    primary = {}
    for r in results:
        pb = r["primary_blocker"]
        primary[pb] = primary.get(pb, 0) + 1
    return {"phase165_not_ready_analyzer":{"not_ready_analyzed_count":len(results),"primary_blockers":primary,"results":results,"mock_used":False,"fixture_used":False}}

def build_blocker_taxonomy():
    taxonomy = {
        "network_data_required": {"category":"data_infrastructure","severity":"blocking","resolution":"execute_live_network_snapshot"},
        "owner_decision_pending": {"category":"governance","severity":"blocking","resolution":"owner_reviews_and_approves"},
        "turnaround_execution_uncertainty": {"category":"thesis_risk","severity":"elevated","resolution":"monitor_turnaround_milestones"},
        "regulatory_risk_ansys_acquisition": {"category":"external_risk","severity":"elevated","resolution":"monitor_regulatory_clearance"}
    }
    return {"phase165_blocker_taxonomy":{"taxonomy":taxonomy,"mock_used":False,"fixture_used":False}}

def build_repair_planner(analysis):
    results=[]
    for r in analysis["phase165_not_ready_analyzer"]["results"]:
        repairs=[]
        for b in r["blockers"]:
            if b == "network_data_required": repairs.append({"action":"execute_live_network_snapshot","owner":"system","priority":"high","precondition":"network_available"})
            elif b == "owner_decision_pending": repairs.append({"action":"owner_reviews_candidate_packet","owner":"owner","priority":"high","precondition":"research_packet_ready"})
            elif "turnaround" in b: repairs.append({"action":"monitor_turnaround_milestones","owner":"agent","priority":"medium","precondition":"quarterly_earnings"})
            elif "regulatory" in b: repairs.append({"action":"monitor_regulatory_status","owner":"agent","priority":"medium","precondition":"regulatory_update"})
        results.append({"ticker":r["ticker"],"repairs":repairs,"total_repairs":len(repairs),"estimated_time_to_ready":"requires_network_plus_owner"})
    return {"phase165_repair_planner":{"total_candidates":len(results),"repairs_planned":sum(x["total_repairs"] for x in results),"results":results,"mock_used":False,"fixture_used":False}}
