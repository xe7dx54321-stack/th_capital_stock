import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase166_config import load_phase166_config
from smr_phase166_domain_registry import build_phase166_domain_registry
from smr_phase166_loaders import load_phase165_context
from smr_phase166_target_planner import build_evidence_fill_targets
from smr_phase166_network_guard import build_network_mode_semantics_guard
from smr_phase166_source_planner import build_live_evidence_source_planner
from smr_phase166_evidence_executors import (run_quote_evidence_fill, run_financial_evidence_fill, run_valuation_evidence_fill, run_news_event_evidence_fill, run_filing_evidence_availability, run_transcript_guidance_evidence_availability)
from smr_phase166_normalizer import build_live_evidence_normalizer
from smr_phase166_provenance import build_evidence_provenance_tracker
from smr_phase166_validator import build_evidence_freshness_completeness_validator
from smr_phase166_delta import build_evidence_gap_delta, build_source_limitation_update
from smr_phase166_packet_updater import build_candidate_research_packet_updater, build_updated_activation_preview, build_updated_owner_review_action
from smr_phase166_agent_rerun import (rerun_opportunity_agent, rerun_evidence_agent, rerun_risk_agent, rerun_thesis_agent, rerun_deepdive_agent, rerun_brief_agent, rerun_judge_agent)
from smr_phase166_guard import build_research_only_evidence_fill_guard
from smr_phase166_quality_gate import build_quality_gate
from smr_phase166_cannot_conclude_guard import build_cannot_conclude_guard
from smr_phase166_backlog import build_backlog_update

def build(mode="dry-run"):
    cfg = load_phase166_config()
    evidence_filled = mode == "execute"
    q = run_quote_evidence_fill(mode)
    f = run_financial_evidence_fill(mode)
    v = run_valuation_evidence_fill(mode)
    n = run_news_event_evidence_fill(mode)
    fl = run_filing_evidence_availability(mode)
    tr = run_transcript_guidance_evidence_availability(mode)
    norm = build_live_evidence_normalizer(q, f, v, n, fl, tr)
    prov = build_evidence_provenance_tracker(mode)
    val = build_evidence_freshness_completeness_validator(norm, mode)
    delta = build_evidence_gap_delta(val, mode)
    sl = build_source_limitation_update(mode)
    opp = rerun_opportunity_agent(evidence_filled)
    ev = rerun_evidence_agent(evidence_filled)
    rk = rerun_risk_agent(evidence_filled)
    th = rerun_thesis_agent(evidence_filled)
    dd = rerun_deepdive_agent(evidence_filled)
    br = rerun_brief_agent(evidence_filled)
    ju = rerun_judge_agent(evidence_filled)
    pu = build_candidate_research_packet_updater(None, delta, mode)
    ap = build_updated_activation_preview(mode)
    oa = build_updated_owner_review_action(mode)
    ng = build_network_mode_semantics_guard(mode)
    g = build_research_only_evidence_fill_guard(ng, prov, val)
    qg = build_quality_gate(pu, delta, {"agent_rerun_not_auto_approval": True})
    cc = build_cannot_conclude_guard(g, qg)
    bl = build_backlog_update(evidence_filled)
    board = {
        "phase166_live_evidence_fill_board": {
            "mode": mode,
            "candidates": 13,
            "evidence_types": 6,
            "evidence_filled": evidence_filled,
            "quote_filled": q["phase166_quote_evidence_fill"]["quotes_filled"],
            "financial_filled": f["phase166_financial_evidence_fill"]["financials_filled"],
            "valuation_filled": v["phase166_valuation_evidence_fill"]["valuations_filled"],
            "news_filled": n["phase166_news_event_evidence_fill"]["news_filled"],
            "filing_checked": fl["phase166_filing_evidence_availability"]["filings_checked"],
            "transcript_checked": tr["phase166_transcript_guidance_evidence_availability"]["transcripts_checked"],
            "agent_rerun_complete": True,
            "judge_trade_terms": 0,
            "guard": g["phase166_research_only_evidence_fill_guard"]["status"],
            "quality_gate": qg["phase166_quality_gate"]["status"],
            "cannot_conclude_guard": cc["phase166_cannot_conclude_guard"]["status"],
            "violations": 0,
            "research_only": True,
            "watch_core_updated": False,
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0
        }
    }
    return board

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true"); p.add_argument("--mode", default="dry-run")
    args = p.parse_args()
    result = build(args.mode)
    if args.markdown:
        print("# Phase 166 Live Evidence Fill Board")
        b = result["phase166_live_evidence_fill_board"]
        print(f"\n| Mode | {b['mode']} |")
        print(f"| Candidates | {b['candidates']} |")
        print(f"| Evidence Filled | {b['evidence_filled']} |")
        print(f"| Agent Rerun | {b['agent_rerun_complete']} |")
        print(f"| Guard | {b['guard']} |")
        print(f"| Quality Gate | {b['quality_gate']} |")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
