import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase170_owner_input_validation_board import build

def build_brief():
    b = build()["phase170_owner_input_validation_board"]
    return {"phase170_owner_input_validation_brief":{"title":"Owner Input Submission Validation Brief","boss_summary":{"clearest_conclusion":"Owner input validation complete; state preview generated without execution.","input_read":b["input_read"],"valid_entries":b["valid_entries"],"quarantined":b["quarantined"],"no_trade_action":True},"analyst_detail":{"state_preview_entries":b["state_preview_entries"],"cannot_conclude":["validated_input_is_not_activation","state_preview_is_not_state_update"]},"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_brief(), ensure_ascii=False, indent=2))
