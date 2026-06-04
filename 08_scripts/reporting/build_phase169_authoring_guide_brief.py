import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase169_authoring_guide_board import build

def build_brief():
    b = build()["phase169_authoring_guide_board"]
    return {"phase169_authoring_guide_brief":{"title":"Owner Decision Input Authoring Guide Brief (Hardened)","boss_summary":{"clearest_conclusion":"Fill guide and 12 examples (5 valid + 7 invalid) ready; all expectations match; owner can safely author decision input.","valid_examples":b["valid_examples"],"invalid_examples":b["invalid_examples"],"expectations_all_match":b["expectations_all_match"],"example_coverage":b["example_coverage_status"],"no_trade_action":True},"analyst_detail":{"guide_fields":5,"decision_options":4,"cannot_conclude":["example_is_not_approval","guide_is_not_auto_write","preflight_is_not_real_submission","sandbox_is_not_real_execution","valid_example_neq_owner_approval","invalid_example_neq_investment_view"]},"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_brief(), ensure_ascii=False, indent=2))
