import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def run(mode="dry-run"):
    from smr_phase162_config import load_phase162_config
    from smr_phase162_domain_registry import build_phase162_domain_registry
    from smr_phase162_loaders import (load_phase153_context, load_phase152_context,
                                       load_phase151_context, load_phase161_context, load_source_fallback_policy)
    from smr_phase162_universe import build_hydration_universe
    from smr_phase162_identity import resolve_candidate_identities
    from smr_phase162_source_planner import plan_candidate_source_routes
    from smr_phase162_hydration import (hydrate_quote_data, hydrate_financial_data,
                                         hydrate_valuation_data, hydrate_news_events)
    from smr_phase162_availability import (check_filing_availability, check_transcript_guidance_availability,
                                            probe_source_availability)
    from smr_phase162_scoring import check_data_freshness, score_hard_data_completeness, score_evidence_readiness
    from smr_phase162_risk_register import build_risk_register
    from smr_phase162_classifier import classify_hydration_status
    from smr_phase162_owner_feed import update_owner_review_feed
    from smr_phase162_agent_queue import update_agent_task_queue
    from smr_phase162_console import build_console_artifact
    from smr_phase162_guard import build_hydration_guard
    from smr_phase162_quality_gate import build_quality_gate
    from smr_phase162_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase162_backlog import build_backlog_update

    config = load_phase162_config()
    domain = build_phase162_domain_registry()
    ctx153 = load_phase153_context()
    ctx152 = load_phase152_context()
    ctx151 = load_phase151_context()
    ctx161 = load_phase161_context()
    policy = load_source_fallback_policy()

    universe = build_hydration_universe()
    targets = universe["phase162_hydration_universe"]["targets"]

    identity = resolve_candidate_identities(targets)
    routes = plan_candidate_source_routes(targets)

    net_mode = "skip-network" if mode == "skip-network" else "ready"
    quote = hydrate_quote_data(targets, net_mode)
    financial = hydrate_financial_data(targets, net_mode)
    valuation = hydrate_valuation_data(targets, net_mode)
    news = hydrate_news_events(targets, net_mode)

    filing = check_filing_availability(targets, net_mode)
    transcript = check_transcript_guidance_availability(targets, net_mode)
    probe = probe_source_availability(targets, net_mode)
    freshness = check_data_freshness(targets, net_mode)
    completeness = score_hard_data_completeness(targets)
    readiness = score_evidence_readiness(targets)
    risk = build_risk_register(targets)
    classifier = classify_hydration_status(targets)
    feed = update_owner_review_feed(targets, readiness)
    queue = update_agent_task_queue(targets, net_mode)
    console = build_console_artifact()
    guard = build_hydration_guard()
    quality = build_quality_gate()
    cc_guard = build_cannot_conclude_guard()
    backlog = build_backlog_update()

    output = {
        "phase162_candidate_hydration_pipeline": {
            "mode": mode,
            "phase": "phase162",
            "strategy": config.get("strategy", ""),
            "research_only": True,
            "targets_total": len(targets),
            "identities_resolved": identity["phase162_identity_resolver"]["identities_resolved"],
            "routes_planned": routes["phase162_source_route_planner"]["targets_planned"],
            "quote_sources": quote["phase162_quote_hydration"]["sources_identified"],
            "financial_available": financial["phase162_financial_hydration"]["financial_available_count"],
            "valuation_available": valuation["phase162_valuation_hydration"]["valuation_available_count"],
            "news_available": news["phase162_news_event_hydration"]["news_available_count"],
            "full_hydration": classifier["phase162_hydration_classifier"]["full_hydration_ready"],
            "partial_hydration": classifier["phase162_hydration_classifier"]["partial_hydration_ready"],
            "blocked": classifier["phase162_hydration_classifier"]["blocked"],
            "full_readiness": readiness["phase162_evidence_readiness_scorer"]["full_readiness"],
            "skip_network_compatible": True,
            "free_sources_only": True,
            "hydration_not_approval": True,
            "data_not_watch_update": True,
            "financial_not_advice": True,
            "valuation_not_target_price": True,
            "news_not_trade_signal": True,
            "guard": guard["phase162_hydration_guard"]["status"],
            "quality_gate": quality["phase162_quality_gate"]["status"],
            "cannot_conclude_guard": cc_guard["phase162_cannot_conclude_guard"]["status"],
            "violations": guard["phase162_hydration_guard"]["violations"],
            "watch_core_updated": False,
            "candidate_auto_activated": False,
            "activation_execution_created": False,
            "target_price_created": 0,
            "mock_used": False, "fixture_used": False,
            "raw_saved": False, "ocr_used": False, "browser_automation_used": False,
            "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
            "trade_recommendation_created": 0, "broker_api_called": False,
            "next_phase_recommendation": backlog["phase162_backlog"]["next_phase_recommendation"]
        }
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output

if __name__ == "__main__":
    mode = "dry-run"
    if "--execute" in sys.argv: mode = "execute"
    elif "--skip-network" in sys.argv: mode = "skip-network"
    run(mode)
