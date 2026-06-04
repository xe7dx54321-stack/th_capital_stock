import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase167_owner_review_board import build

def build_brief():
    board = build()
    b = board["phase167_owner_review_board"]
    return {
        "phase167_owner_review_brief": {
            "title": "Owner Review Packet Console Brief",
            "boss_summary": {
                "clearest_conclusion": "13 candidate review packets ready for owner review; no auto-activation, no trade output.",
                "review_cards": b["review_cards"],
                "decision_prep_packages": b["decision_prep_packages"],
                "console_ready": b["console_page"],
                "no_trade_action": True
            },
            "analyst_detail": {
                "coverage": "13 US-listed semiconductor/technology candidates",
                "comparison_matrix_ready": b["comparison_matrix_ready"],
                "input_drafts": b["input_drafts"],
                "cannot_conclude": [
                    "owner_review_packet_is_not_owner_approval",
                    "decision_prep_is_not_activation_execution",
                    "comparison_matrix_is_not_investment_ranking",
                    "draft_is_not_final_owner_decision"
                ]
            },
            "mock_used": False,
            "fixture_used": False
        }
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    result = build_brief()
    if args.markdown:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
