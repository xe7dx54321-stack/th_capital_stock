CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
EVIDENCE_TYPES = ["quote","financial","valuation","news_event","filing_availability","transcript_guidance"]

def build_evidence_fill_targets():
    targets = []
    for tk in CANDIDATES:
        for et in EVIDENCE_TYPES:
            targets.append({
                "ticker": tk,
                "evidence_type": et,
                "source": "SEC_EDGAR" if et in ["financial","filing_availability","transcript_guidance"] else ("Yahoo_Finance" if et == "quote" else "Alpha_Vantage"),
                "status": "planned",
                "network_required": True,
                "fallback_available": True,
                "cannot_conclude": ["planned_evidence_is_not_live_evidence", "status_planned_means_not_yet_fetched"]
            })
    minimum_targets = sum(1 for t in targets if t["evidence_type"] in ["quote","financial","valuation"])
    preferred_targets = len(targets)
    return {
        "phase166_evidence_fill_targets": {
            "total_targets": len(targets),
            "evidence_fill_targets": minimum_targets,
            "minimum_targets_met": minimum_targets >= 39,
            "preferred_targets_met": preferred_targets >= 78,
            "targets": targets,
            "mock_used": False,
            "fixture_used": False
        }
    }
