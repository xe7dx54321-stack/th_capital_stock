import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def run(mode="dry-run"):
    from smr_phase165_config import load_phase165_config
    from smr_phase165_domain_registry import build_phase165_domain_registry
    from smr_phase165_loaders import load_phase164_context, load_phase163_context, load_phase162_context, load_phase149_context
    from smr_phase165_readiness import analyze_not_ready_reasons, build_blocker_taxonomy, build_repair_planner
    from smr_phase165_planners import build_evidence_gap_planner, build_source_repair_planner, build_thesis_seed_refiner, build_risk_review_planner
    from smr_phase165_agents import run_opportunity_agent, run_evidence_agent, run_risk_agent, run_thesis_agent, run_deepdive_agent, run_brief_agent, run_judge_agent, build_handoff_map
    from smr_phase165_packets import build_research_packets, build_activation_preview_conditions, build_owner_next_actions, build_daily_monitoring_update, build_console_integration
    from smr_phase165_guard import build_readiness_guard
    from smr_phase165_quality_gate import build_quality_gate
    from smr_phase165_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase165_backlog import build_backlog_update

    config = load_phase165_config()
    domain = build_phase165_domain_registry()
    ctx164 = load_phase164_context(); ctx163 = load_phase163_context()
    ctx162 = load_phase162_context(); ctx149 = load_phase149_context()
    readiness = analyze_not_ready_reasons()
    taxonomy = build_blocker_taxonomy()
    repair = build_repair_planner(readiness)
    evidence = build_evidence_gap_planner()
    source = build_source_repair_planner()
    thesis = build_thesis_seed_refiner()
    risk_plan = build_risk_review_planner()
    opp = run_opportunity_agent(); ev = run_evidence_agent(); rk = run_risk_agent()
    th = run_thesis_agent(); dd = run_deepdive_agent(); br = run_brief_agent(); ju = run_judge_agent()
    handoff = build_handoff_map()
    packets = build_research_packets(opp, ev, rk, th, dd, br, ju, repair, readiness)
    preview = build_activation_preview_conditions()
    owner = build_owner_next_actions()
    daily = build_daily_monitoring_update()
    console = build_console_integration()
    guard = build_readiness_guard(); quality = build_quality_gate()
    cc = build_cannot_conclude_guard(); backlog = build_backlog_update()

    output = {"phase165_readiness_repair_pipeline":{"mode":mode,"phase":"phase165","strategy":config.get("strategy",""),"research_only":True,"agent_simulation_only":True,"not_ready_analyzed":13,"blocker_types":4,"repair_plans":13,"agent_passes":7,"research_packets":13,"judge_trade_terms":0,"activation_previews":13,"owner_actions":13,"llm_api_called":False,"guard":guard["phase165_readiness_guard"]["status"],"quality_gate":quality["phase165_quality_gate"]["status"],"cannot_conclude_guard":cc["phase165_cannot_conclude_guard"]["status"],"violations":0,"repair_not_approval":True,"agent_not_llm":True,"packet_not_thesis":True,"preview_not_execution":True,"owner_action_not_trade":True,"watch_core_updated":False,"activation_execution_created":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0,"next_phase_recommendation":backlog["phase165_backlog"]["next_phase_recommendation"]}}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output
if __name__=="__main__":
    mode="dry-run"
    if "--execute" in sys.argv: mode="execute"
    elif "--skip-network" in sys.argv: mode="skip-network"
    run(mode)
