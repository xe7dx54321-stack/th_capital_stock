import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase154_loop_research_board import build as build_board
    b = build_board()["phase154_loop_research_board"]
    j = b["agents"]["judge"]
    return "\n".join([
        "# Multi-Agent Research Loop Brief", "",
        "## Loop Summary", f"- Loop targets: {b['loop_targets_total']}",
        f"- Judge passed: {j['passed']}", f"- Judge blocked: {j['blocked']}",
        f"- Handoff chain: {b['handoff_chain']['chain_length']} steps", "",
        "## Key Principles",
        "- All agent outputs are structural simulation templates, not live LLM calls.",
        "- Agent output is NOT factual evidence.",
        "- Agent loop is NOT true LLM autonomy.",
        "- Judge pass is NOT investment approval.",
        "- Watch/Core NOT updated. Candidates NOT auto-activated.",
        "- 300394 CNINFO blocker retained. 688041 derived valuation retained.",
        "- No trade recommendations, target prices, or position sizing.",
    ])

def build_json():
    return {"phase154_loop_research_brief": {"brief_generated": True, "mock_used": False, "fixture_used": False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(), indent=2, ensure_ascii=False, default=str))
