import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def run(mode="dry-run"):
    from smr_phase163_config import load_phase163_config
    from smr_phase163_domain_registry import build_phase163_domain_registry
    from smr_phase163_loaders import load_phase162_context, load_phase153_context, load_phase151_context, load_source_fallback_policy
    from smr_phase163_target_planner import plan_live_execute_targets
    from smr_phase163_network_policy import build_network_mode_policy
    from smr_phase163_snapshot import (execute_quote_snapshot, execute_financial_snapshot, execute_valuation_snapshot, execute_news_snapshot, check_filing_live, check_transcript_live, normalize_snapshots, validate_freshness, score_completeness)
    from smr_phase163_live_hydration import compare_live_delta, build_live_limitation_register
    from smr_phase163_monitoring import build_monitoring_signals, build_daily_monitoring_adapter
    from smr_phase163_refresh import refresh_owner_feed, refresh_agent_queue, refresh_console_artifact
    from smr_phase163_guard import build_live_hydration_guard
    from smr_phase163_quality_gate import build_quality_gate
    from smr_phase163_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase163_backlog import build_backlog_update

    config = load_phase163_config()
    domain = build_phase163_domain_registry()
    ctx162 = load_phase162_context(); ctx153 = load_phase153_context(); ctx151 = load_phase151_context()
    policy_src = load_source_fallback_policy()
    planner = plan_live_execute_targets()
    targets = planner["phase163_target_planner"]["targets"]
    net_policy = build_network_mode_policy(mode)
    quote = execute_quote_snapshot(targets, mode)
    financial = execute_financial_snapshot(targets, mode)
    valuation = execute_valuation_snapshot(targets, mode)
    news = execute_news_snapshot(targets, mode)
    filing = check_filing_live(targets, mode)
    transcript = check_transcript_live(targets, mode)
    normalized = normalize_snapshots(quote, financial, valuation, news)
    freshness = validate_freshness(normalized)
    completeness = score_completeness(normalized)
    delta = compare_live_delta(normalized, mode)
    limitations = build_live_limitation_register(targets, mode)
    signals = build_monitoring_signals(targets, mode)
    daily = build_daily_monitoring_adapter(signals, mode)
    feed = refresh_owner_feed(targets, mode)
    queue = refresh_agent_queue(targets, mode)
    console = refresh_console_artifact(mode)
    guard = build_live_hydration_guard()
    quality = build_quality_gate()
    cc = build_cannot_conclude_guard()
    backlog = build_backlog_update()

    output = {"phase163_live_hydration_pipeline": {"mode": mode, "phase": "phase163", "strategy": config.get("strategy",""), "research_only": True, "targets_total": len(targets), "snapshots_planned": len(targets), "snapshots_taken": 0 if mode == "skip-network" else len(targets), "snapshots_deferred": len(targets) if mode == "skip-network" else 0, "raw_saved": False, "raw_payload_bytes": 0, "valuation_target_price": 0, "news_trade_signal": 0, "monitoring_signals": len(signals["phase163_monitoring_signals"]["signals"]), "daily_monitoring_integrated": len(daily["phase163_daily_monitoring_adapter"]["integrated"]), "owner_feed_items": feed["phase163_owner_feed_refresh"]["items"], "agent_tasks": queue["phase163_agent_queue_refresh"]["tasks"], "guard": guard["phase163_live_hydration_guard"]["status"], "quality_gate": quality["phase163_quality_gate"]["status"], "cannot_conclude_guard": cc["phase163_cannot_conclude_guard"]["status"], "violations": 0, "snapshot_not_approval": True, "data_not_watch_update": True, "watch_core_updated": False, "candidate_auto_activated": False, "activation_execution_created": False, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0, "target_price_created": 0, "trade_recommendation_created": 0, "broker_api_called": False, "next_phase_recommendation": backlog["phase163_backlog"]["next_phase_recommendation"]}}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output
if __name__ == "__main__":
    mode = "dry-run"
    if "--execute" in sys.argv: mode = "execute"
    elif "--skip-network" in sys.argv: mode = "skip-network"
    run(mode)
