import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_validation_board import build_validation_board
from smr_phase128_source_validation_gap_register import build_source_validation_gap_register

def build_validation_brief_md(skip_network=False):
    board=build_validation_board(skip_network)["phase128_validation_board"]
    gaps=build_source_validation_gap_register(skip_network)["phase128_source_validation_gap_register"]
    L=[]
    L.append("# External Source Validation Report")
    L.append("")
    L.append("## Summary")
    L.append(f"- {board['sources_probed']} external sources probed")
    L.append(f"- Pending before: {board['pending_before']} -> after: {board['pending_after']}")
    for sec,data in board["sections"].items():
        L.append(f"- {sec}: {data['count']}")
    L.append("")
    L.append("## Available Sources")
    if "available" in board["sections"]:
        for item in board["sections"]["available"]["items"]:
            L.append(f"- {item['source_id']} ({item['market']}): available")
    L.append("")
    L.append("## Blocked / Unavailable Sources")
    for sec in ["blocked","unsupported","degraded"]:
        if sec in board["sections"]:
            for item in board["sections"][sec]["items"]:
                L.append(f"- {item['source_id']}: {sec}" + (f" - {item['error']}" if item.get('error') else ""))
    L.append("")
    L.append("## Manual Required")
    if "manual_required" in board["sections"]:
        for item in board["sections"]["manual_required"]["items"]:
            L.append(f"- {item['source_id']}: requires manual action")
    L.append("")
    L.append("## Known Gaps Retained")
    for g in gaps["gaps"]:
        if g.get("retained_from_phase127"):
            L.append(f"- {g['source_id']} ({g['tickers']}): {g['most_specific_blocker']}")
    L.append("")
    L.append("*Probe complete. Research-only. No trade recommendations.*")
    import os as _os
    return _os.linesep.join(L)
