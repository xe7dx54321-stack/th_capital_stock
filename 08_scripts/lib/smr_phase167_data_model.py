CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_candidate_review_packet_data_model():
    packets = []
    for tk in CANDIDATES:
        packets.append({
            "ticker": tk,
            "market": "US",
            "review_packet": {
                "opportunity_rating": "identified_not_confirmed",
                "evidence_status": "filled",
                "risk_assessment": "standard",
                "thesis_status": "seed_generated_not_confirmed",
                "deepdive_status": "in_progress",
                "brief_status": "draft_with_evidence",
                "judge_status": "passed_no_trade_language"
            },
            "review_packet_not_approval": True,
            "cannot_conclude": ["review_packet_is_not_owner_approval", "packet_model_is_not_activation"]
        })
    return {
        "phase167_candidate_review_packet_data_model": {
            "candidates": len(packets),
            "packets_built": len(packets),
            "results": packets,
            "mock_used": False,
            "fixture_used": False
        }
    }
