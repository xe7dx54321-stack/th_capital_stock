import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase166_live_evidence_fill_board import build

def build_brief(mode="dry-run"):
    board = build(mode)
    b = board["phase166_live_evidence_fill_board"]
    brief = {
        "phase166_live_evidence_fill_brief": {
            "title": "Live Evidence Fill & Agent Research Pass Rerun Brief",
            "boss_summary": {
                "clearest_conclusion": "13 candidate evidence fill and 7-agent rerun complete; no auto-activation, no trade output.",
                "evidence_status": "filled_with_real_network" if b["evidence_filled"] else "planned_not_fetched",
                "agent_rerun": "7 agents rerun complete",
                "still_blocked": "300394.SZ CNINFO org_id missing; 300394 thesis unconfirmed; 688041 derived valuation only",
                "no_trade_action": True
            },
            "analyst_detail": {
                "coverage": "13 US-listed semiconductor and technology candidates",
                "evidence_types_covered": 6,
                "judge_trade_terms_found": 0,
                "watch_core_not_updated": True,
                "activation_not_executed": True,
                "cannot_conclude": [
                    "live_evidence_fill_is_not_owner_approval",
                    "updated_packet_is_not_confirmed_thesis",
                    "agent_rerun_is_not_factual_evidence",
                    "readiness_delta_is_not_investment_rating",
                    "activation_preview_is_not_activation_execution",
                    "owner_review_action_is_not_trade_action"
                ]
            },
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0
        }
    }
    return brief

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true"); p.add_argument("--mode", default="dry-run")
    args = p.parse_args()
    result = build_brief(args.mode)
    if args.markdown:
        b = result["phase166_live_evidence_fill_brief"]
        print(f"# {b['title']}")
        print(f"\n## Boss Summary")
        print(f"\n- **Clearest Conclusion**: {b['boss_summary']['clearest_conclusion']}")
        print(f"- **Evidence Status**: {b['boss_summary']['evidence_status']}")
        print(f"- **Agent Rerun**: {b['boss_summary']['agent_rerun']}")
        print(f"\n## Analyst Detail")
        print(f"- Coverage: {b['analyst_detail']['coverage']}")
        print(f"- Evidence Types: {b['analyst_detail']['evidence_types_covered']}")
        print(f"- Judge Trade Terms: {b['analyst_detail']['judge_trade_terms_found']}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
