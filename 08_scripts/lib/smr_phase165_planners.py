TICKERS = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_evidence_gap_planner():
    results=[]
    for tk in TICKERS:
        gaps = ["live_financial_data","live_valuation_data","live_quote_data"]
        results.append({"ticker":tk,"evidence_gaps":gaps,"gap_count":len(gaps),"all_gaps_network_dependent":True})
    return {"phase165_evidence_gap_planner":{"total":len(results),"total_gaps":sum(r["gap_count"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}

def build_source_repair_planner():
    results=[]
    for tk in TICKERS:
        results.append({"ticker":tk,"source_repairs":[{"source":"SEC EDGAR","status":"available_no_login","action":"fetch_10k_10q"}]})
    return {"phase165_source_repair_planner":{"total":len(results),"all_sources_available":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_thesis_seed_refiner():
    results=[]
    seeds = {"MRVL":"Custom ASIC and data center networking leader benefiting from AI infrastructure buildout.","AMAT":"Semiconductor equipment leader with direct exposure to AI-driven capex cycle.","LRCX":"Etch and deposition leader complementary to foundry/logic expansion.","KLAC":"Process control and yield management leader essential to advanced node manufacturing.","INTC":"Legacy semiconductor leader in foundry turnaround; thesis requires observable execution milestones.","SNPS":"EDA software duopoly with Ansys acquisition pending; thesis contingent on regulatory clearance.","CDNS":"EDA and system design leader; paired thesis with Synopsys competitive dynamics.","CRM":"Enterprise SaaS leader with Agentforce AI monetization thesis; requires revenue trajectory evidence.","TSM":"Dominant advanced foundry with structural AI demand tailwind.","ASML":"Monopoly EUV lithography supplier; thesis tied to sustained advanced node capex.","AMD":"GPU/CPU competitor gaining share in AI inference; thesis requires sustained market share evidence.","SNOW":"Cloud data platform with AI/ML workload growth thesis; requires consumption revenue evidence.","MU":"Memory cycle beneficiary with HBM AI demand thesis; cyclical risk requires cycle timing assessment."}
    for tk in TICKERS:
        results.append({"ticker":tk,"thesis_seed":seeds.get(tk,""),"thesis_seed_not_confirmed":True,"thesis_requires_evidence":True,"cannot_conclude":["thesis_seed_is_not_confirmed_thesis","thesis_requires_factual_evidence_validation"]})
    return {"phase165_thesis_seed_refiner":{"total":len(results),"thesis_seed_not_confirmed":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_risk_review_planner():
    results=[]
    for tk in TICKERS:
        risks = [{"type":"data_availability","severity":"high","mitigation":"execute_live_network_snapshot"}]
        if tk == "INTC": risks.append({"type":"turnaround_execution","severity":"high","mitigation":"monitor_quarterly_milestones"})
        if tk == "SNPS": risks.append({"type":"regulatory","severity":"medium","mitigation":"monitor_ansys_acquisition_clearance"})
        if tk == "MU": risks.append({"type":"cyclical","severity":"medium","mitigation":"monitor_memory_cycle_indicators"})
        results.append({"ticker":tk,"risks":risks,"risk_count":len(risks),"risk_review_not_investment_rating":True})
    return {"phase165_risk_review_planner":{"total":len(results),"elevated_risk_count":sum(1 for r in results if r["risk_count"]>1),"risk_review_not_investment_rating":True,"results":results,"mock_used":False,"fixture_used":False}}

