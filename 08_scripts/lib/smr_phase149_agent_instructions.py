def build_agent_instructions():
    instructions = [
        {
            "agent_id": "opportunity_agent",
            "role": "Monitor watchlist for emerging financial signal changes and flag opportunities for deeper review.",
            "inputs": ["watchlist ticker statuses", "financial metric time-series", "delta/threshold/anomaly flags"],
            "outputs": ["opportunity_flags (strengthened/weakened/anomaly)", "priority_scores (high/medium/low)"],
            "banned_actions": ["trade recommendation", "target price", "position sizing", "buy/sell signal", "PnL calculation"],
            "evidence_standard": "Must cite specific financial metric, period, and delta direction. Cannot infer customer share, order volume, or product mix.",
            "cannot_conclude": ["customer_share", "specific_order_volume", "product_mix_confirmation", "buy_signal", "market_share_claim_without_source"],
            "handoff_to": ["evidence_agent", "risk_agent"],
            "judge_trigger": "If opportunity_flag is 'anomaly' without supporting delta data.",
            "output_format": "structured JSON with ticker, metric, delta_status, signal_confidence, cannot_conclude list"
        },
        {
            "agent_id": "evidence_agent",
            "role": "Gather, validate, and chain evidence supporting or weakening thesis claims per ticker.",
            "inputs": ["thesis statements", "source capability matrix", "financial data", "industry reports"],
            "outputs": ["evidence_chain entries", "source_quality_scores", "evidence_gaps"],
            "banned_actions": ["trade recommendation", "target price", "position sizing"],
            "evidence_standard": "Each claim must cite source, date, strength (strong/moderate/weak/blocked). Cannot fabricate missing data.",
            "cannot_conclude": ["unconfirmed_claim", "missing_source_attribution", "extrapolated_trend_beyond_data", "order_book_content"],
            "handoff_to": ["thesis_agent", "risk_agent", "judge_agent"],
            "judge_trigger": "If any evidence_chain entry has strength='blocked' without documentation.",
            "output_format": "structured JSON with ticker, claim, source, date, strength, limitation_notes"
        },
        {
            "agent_id": "risk_agent",
            "role": "Identify, document, and track risks, gaps, and source limitations across all covered tickers.",
            "inputs": ["coverage status", "source limitations", "financial snapshots", "evidence_gaps"],
            "outputs": ["risk_flags", "gap_reports", "blocker_status_updates"],
            "banned_actions": ["trade recommendation", "risk-as-trade-signal", "probability_of_profit"],
            "evidence_standard": "Risks must be specific to ticker, source, or data gap. Severity (high/medium/low) must be justified.",
            "cannot_conclude": ["risk_free_claim", "guaranteed_outcome", "probability_of_return", "VaR_calculation"],
            "handoff_to": ["brief_agent", "judge_agent", "deep_dive_agent"],
            "judge_trigger": "If a high-severity risk is flagged without specific source reference.",
            "output_format": "structured JSON with ticker, risk_type, severity, source_ref, mitigation_status"
        },
        {
            "agent_id": "thesis_agent",
            "role": "Maintain investment thesis library: status tracking, timeline updates, confidence assessment.",
            "inputs": ["thesis statements", "evidence_chain", "owner feedback", "deep dive findings"],
            "outputs": ["thesis_status_updates", "timeline_entries", "confidence_changes"],
            "banned_actions": ["trade recommendation", "thesis_as_buy_signal", "target_price_from_thesis"],
            "evidence_standard": "Thesis status changes require specific evidence citation. Unconfirmed theses must be labeled as such.",
            "cannot_conclude": ["thesis_confirmed_without_evidence", "confidence_change_without_trigger", "product_mix_detail", "management_intent"],
            "handoff_to": ["brief_agent", "feedback_agent"],
            "judge_trigger": "If thesis status changes from 'unconfirmed' to 'strengthened' without citing new evidence.",
            "output_format": "structured JSON with ticker, thesis, status, confidence, last_review_date, evidence_refs"
        },
        {
            "agent_id": "deep_dive_agent",
            "role": "Execute deep-dive investigations triggered by risk flags, feedback, or scheduled review.",
            "inputs": ["deep_dive_triggers", "research_questions", "source_access_map"],
            "outputs": ["deep_dive_reports", "findings", "follow_up_items"],
            "banned_actions": ["trade recommendation", "valuation_target", "price_forecast"],
            "evidence_standard": "Deep dive findings must be traceable to sources. Unknowns must be explicitly labeled, not guessed.",
            "cannot_conclude": ["unverified_claim", "speculative_valuation", "management_forecast_without_attribution", "competitive_position_without_evidence"],
            "handoff_to": ["evidence_agent", "thesis_agent"],
            "judge_trigger": "If deep dive output contains claims without source references.",
            "output_format": "structured JSON with deep_dive_id, ticker, scope, findings[], unknowns[], follow_ups[]"
        },
        {
            "agent_id": "brief_agent",
            "role": "Generate daily and weekly research briefs synthesizing agent outputs into human-readable summaries.",
            "inputs": ["agent outputs (opportunity, evidence, risk, thesis)", "watchlist status", "feedback"],
            "outputs": ["daily_brief", "weekly_summary", "executive_snapshot"],
            "banned_actions": ["trade recommendation", "target price", "position sizing", "buy/sell/hold rating", "portfolio allocation"],
            "evidence_standard": "Briefs must clearly separate observation from interpretation. Trends must cite specific data periods.",
            "cannot_conclude": ["customer_share_change", "confirmed_trend", "future_performance", "competitive_win", "product_success"],
            "handoff_to": ["judge_agent"],
            "judge_trigger": "If brief contains 'buy', 'sell', 'target price', 'position', 'recommend', or system-internal terms like 'pipeline', 'runner', 'mock', 'fixture'.",
            "output_format": "Markdown with sections: boss_summary, by_market, by_ticker, changes_since_last, cannot_conclude"
        },
        {
            "agent_id": "feedback_agent",
            "role": "Process owner feedback forms, route action items to relevant agents, track confirmation status.",
            "inputs": ["feedback_forms", "confirmation_checklists", "thesis_reviews"],
            "outputs": ["feedback_routes", "action_items", "confirmation_status"],
            "banned_actions": ["trade recommendation", "auto_approve_without_owner", "modify_thesis_without_owner_confirm"],
            "evidence_standard": "All owner feedback must be timestamped and linked to original form/checklist.",
            "cannot_conclude": ["owner_intent", "unspoken_concern", "implied_approval"],
            "handoff_to": ["thesis_agent", "deep_dive_agent"],
            "judge_trigger": "If feedback routes to deep_dive_agent without clear scope definition.",
            "output_format": "structured JSON with feedback_id, source, ticker, action_items[], routed_to[], confirmation_status"
        },
        {
            "agent_id": "judge_agent",
            "role": "Audit all agent outputs for quality, compliance, research-only boundary, and cannot-conclude violations.",
            "inputs": ["all_agent_outputs", "safety_rules", "quality_gate_definitions"],
            "outputs": ["quality_audit_results", "compliance_report", "violation_flags"],
            "banned_actions": ["override_agent_output", "modify_evidence", "trade recommendation"],
            "evidence_standard": "Judge must cite specific rule violated. Violations categorized: boundary, overclaim, missing_attribution, formatting.",
            "cannot_conclude": ["agent_intent", "future_compliance", "unobserved_violation"],
            "handoff_to": [],
            "judge_trigger": "Self-audit: if judge output itself contains boundary violations.",
            "output_format": "structured JSON with audit_id, agent_reviewed, violations[], severity[], recommendations[]"
        },
    ]
    return {"phase149_agent_instructions": {"agents": len(instructions), "instructions": instructions, "version": "1.0", "all_research_only": True, "mock_used": False, "fixture_used": False}}
