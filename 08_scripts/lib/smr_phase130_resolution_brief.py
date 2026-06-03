import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_resolution_board import build_resolution_board
from smr_phase130_manual_action_template import build_manual_action_template

def build_resolution_brief_md():
    board=build_resolution_board()["phase130_resolution_board"]
    manual=build_manual_action_template()["phase130_manual_action_template"]
    L=[]
    L.append("# 300394 CNINFO Blocker Resolution Report")
    L.append("")
    L.append("## Blocker Summary")
    L.append(f"- Ticker: 300394.SZ (Tianfu Communication)")
    L.append(f"- Original blocker: cninfo_org_id_missing")
    L.append(f"- Blocker persisted since: Phase 82")
    L.append(f"- Current status: partially resolved via alternative source mapping")
    L.append("")
    L.append("## Key Finding")
    L.append("CNINFO org_id for 300394 could not be automatically discovered without browser automation or manual search.")
    L.append("However, alternative disclosure sources can provide equivalent financial data:")
    L.append("- SZSE official exchange page: company announcements and filings")
    L.append("- Eastmoney: aggregated financial data (mirrors CNINFO)")
    L.append("- CNINFO IRM: investor Q&A interactions")
    L.append("- Company IR website: official company publications")
    L.append("")
    L.append("## Owner Action Required")
    for step in manual["owner_checklist"]:
        L.append(f"{step['step']}. [{step['priority'].upper()}] {step['action']}")
        L.append(f"   URL: {step.get('url','N/A')}")
    L.append("")
    L.append("## Resolution Decision")
    L.append("Recommended: integrate 300394 via Eastmoney as alternative data source.")
    L.append("If owner confirms Eastmoney page works, system can integrate in next phase.")
    L.append("")
    L.append("*Research-only. No trade recommendations. No target prices.*")
    import os as _os
    return _os.linesep.join(L)


