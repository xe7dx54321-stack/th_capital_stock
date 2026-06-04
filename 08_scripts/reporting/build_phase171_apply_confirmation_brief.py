import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase171_apply_confirmation_board import build

def build_brief():
    b = build()["phase171_apply_confirmation_board"]
    return {"phase171_apply_confirmation_brief":{"title":"Owner Final Apply Confirmation Brief","boss_summary":{"clearest_conclusion":"Apply package ready; awaiting owner final confirmation. No state update executed.","apply_ready":b["apply_ready"],"activated_would_be":b["activated"],"no_trade_action":True},"analyst_detail":{"rollback_prepared":b["rollback_prepared"],"checklist_items":b["checklist_items"],"cannot_conclude":["confirmation_gate_is_not_apply","apply_package_is_not_execution"]},"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_brief(), ensure_ascii=False, indent=2))
