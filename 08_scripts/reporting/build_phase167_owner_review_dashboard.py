import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase167_owner_review_board import build

def build_dashboard():
    board = build()
    b = board["phase167_owner_review_board"]
    return {
        "phase167_owner_review_dashboard": {
            "summary": {
                "candidates": b["candidates"],
                "review_cards": b["review_cards"],
                "decision_prep_packages": b["decision_prep_packages"],
                "input_drafts": b["input_drafts"],
                "console_page": b["console_page"],
                "link_integrity": b["link_integrity"],
                "ui_safety": b["ui_safety"],
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
                "next_phase_recommendation": "Phase 168: Owner submits decisions; system executes activation into formal research coverage per owner input."
            }
        }
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    result = build_dashboard()
    if args.markdown:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
