import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def run(mode="dry-run"):
    from smr_phase164_config import load_phase164_config
    from smr_phase164_domain_registry import build_phase164_domain_registry
    from smr_phase164_loaders import load_phase163_context, load_phase162_context, load_phase158_context, load_phase146_context
    from smr_phase164_network_semantics import resolve_network_mode_semantics
    from smr_phase164_console_data import (build_console_data_model, build_summary_panel, build_hydration_cards, build_snapshot_detail_panel, build_freshness_completeness_panel, build_limitation_panel, build_monitoring_signal_panel, build_owner_feed_panel, build_agent_queue_panel, build_daily_monitoring_panel, build_ui_safety_copy, build_link_integrity)
    from smr_phase164_agent_bridge import build_agent_loop_bridge, build_scheduling_preview
    from smr_phase164_activation_precheck import build_activation_precheck
    from smr_phase164_console_page import build_console_page_html, build_nav_integration, build_css_extension
    from smr_phase164_guard import build_console_guard
    from smr_phase164_quality_gate import build_quality_gate
    from smr_phase164_cannot_conclude_guard import build_cannot_conclude_guard
    from smr_phase164_backlog import build_backlog_update

    config = load_phase164_config()
    domain = build_phase164_domain_registry()
    ctx163 = load_phase163_context(); ctx162 = load_phase162_context()
    ctx158 = load_phase158_context(); ctx146 = load_phase146_context()
    semantics = resolve_network_mode_semantics(mode)
    data = build_console_data_model(mode)
    summary = build_summary_panel(data)
    cards = build_hydration_cards(data)
    details = build_snapshot_detail_panel(data)
    freshness = build_freshness_completeness_panel(data)
    limitation = build_limitation_panel()
    monitoring = build_monitoring_signal_panel(data)
    feed = build_owner_feed_panel()
    queue = build_agent_queue_panel()
    daily = build_daily_monitoring_panel()
    activation = build_activation_precheck(mode)
    bridge = build_agent_loop_bridge(mode)
    schedule = build_scheduling_preview(mode)
    console = build_console_page_html(); nav = build_nav_integration(); css = build_css_extension()
    safety = build_ui_safety_copy(); links = build_link_integrity()
    guard = build_console_guard(); quality = build_quality_gate()
    cc = build_cannot_conclude_guard(); backlog = build_backlog_update()

    output = {"phase164_hydration_console_pipeline": {"mode": mode, "phase": "phase164", "strategy": config.get("strategy",""), "research_only": True, "cards": cards["phase164_hydration_cards"]["cards_count"], "panels": 10, "console_page": True, "static_html": True, "ui_safety": safety["phase164_ui_safety_copy"]["overall_status"], "link_integrity": links["phase164_link_integrity"]["overall_status"], "guard": guard["phase164_console_guard"]["status"], "quality_gate": quality["phase164_quality_gate"]["status"], "cannot_conclude_guard": cc["phase164_cannot_conclude_guard"]["status"], "violations": 0, "console_not_approval": True, "snapshot_not_watch_update": True, "monitoring_not_trade": True, "precheck_not_execution": True, "llm_api_called": False, "watch_core_updated": False, "activation_execution_created": False, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0, "target_price_created": 0, "next_phase_recommendation": backlog["phase164_backlog"]["next_phase_recommendation"]}}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output
if __name__ == "__main__":
    mode = "dry-run"
    if "--execute" in sys.argv: mode = "execute"
    elif "--skip-network" in sys.argv: mode = "skip-network"
    run(mode)
