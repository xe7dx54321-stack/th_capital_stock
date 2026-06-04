import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase166_live_evidence_fill_board import build

def build_dashboard(mode="dry-run"):
    board = build(mode)
    b = board["phase166_live_evidence_fill_board"]
    dashboard = {
        "phase166_live_evidence_fill_dashboard": {
            "summary": {
                "mode": b["mode"],
                "candidates": b["candidates"],
                "evidence_types": b["evidence_types"],
                "evidence_filled": b["evidence_filled"],
                "quote_filled": b["quote_filled"],
                "financial_filled": b["financial_filled"],
                "valuation_filled": b["valuation_filled"],
                "news_filled": b["news_filled"],
                "filing_checked": b["filing_checked"],
                "transcript_checked": b["transcript_checked"],
                "agent_rerun_complete": b["agent_rerun_complete"],
                "judge_trade_terms": b["judge_trade_terms"],
                "guard": b["guard"],
                "quality_gate": b["quality_gate"],
                "cannot_conclude_guard": b["cannot_conclude_guard"],
                "violations": b["violations"],
                "watch_core_updated": b["watch_core_updated"],
                "research_only": b["research_only"],
                "mock_used": b["mock_used"],
                "fixture_used": b["fixture_used"],
                "pending_created": b["pending_created"],
                "paper_order_created": b["paper_order_created"],
                "real_trade_created": b["real_trade_created"],
                "target_price_created": b["target_price_created"],
                "next_phase_recommendation": "Phase 167: Owner reviews updated research packets and decides which candidates to activate into formal research coverage."
            }
        }
    }
    return dashboard

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true"); p.add_argument("--mode", default="dry-run")
    args = p.parse_args()
    result = build_dashboard(args.mode)
    if args.markdown:
        print("# Phase 166 Live Evidence Fill Dashboard")
        s = result["phase166_live_evidence_fill_dashboard"]["summary"]
        for k, v in s.items():
            print(f"- {k}: {v}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
