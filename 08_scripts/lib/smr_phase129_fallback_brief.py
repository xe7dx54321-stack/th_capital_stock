import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_board import build_fallback_board
from smr_phase129_gap_register import build_gap_register

def build_fallback_brief_md(skip_network=False):
    board=build_fallback_board(skip_network)["phase129_fallback_board"]
    gaps=build_gap_register(skip_network)["phase129_gap_register"]
    L=[]
    L.append("# Official Source Fallback Resolution Report")
    L.append("")
    L.append("## Summary")
    L.append(f"- {board['sources_total']} blocked/degraded official sources addressed")
    L.append(f"- {board['resolved']} resolved via third-party equivalents")
    L.append(f"- {board['manual_required']} require manual workflow")
    L.append(f"- {board['blockers_retained']} known blockers retained")
    L.append("")
    L.append("## Resolved via Third-Party Equivalents")
    for r in board["sections"]["resolved_via_fallback"]:
        L.append(f"- {r['source_id']}: resolved via {r['recommended_source']} ({r.get('note','')})")
    L.append("")
    L.append("## Manual Workflow Required")
    for r in board["sections"]["manual_workflow_required"]:
        L.append(f"- {r['source_id']}: manual only ({r.get('note','')})")
    L.append("")
    L.append("## Retained Known Blockers")
    for g in gaps["gaps"]:
        if g.get("retained_from_phase128"):
            L.append(f"- {g['id']} ({g['tickers']}): {g['status']} ({g['severity']})")
    L.append("")
    L.append("*Fallback strategy complete. Research-only. No trade recommendations.*")
    import os as _os
    return _os.linesep.join(L)
