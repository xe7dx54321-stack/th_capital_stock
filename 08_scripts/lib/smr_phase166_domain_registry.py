def build_phase166_domain_registry():
    return {
        "phase166_domain_registry": {
            "domains": [
                {"domain": "live_evidence_fill", "description": "Real network structured evidence fill for 13 candidates across 6 evidence types", "status": "active"},
                {"domain": "agent_research_pass_rerun", "description": "Rerun 7 Agent candidate passes with filled evidence", "status": "active"},
                {"domain": "evidence_provenance_tracking", "description": "Track evidence source, freshness, completeness for every filled item", "status": "active"}
            ],
            "candidates": ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"],
            "evidence_types": ["quote","financial","valuation","news_event","filing_availability","transcript_guidance"],
            "mock_used": False,
            "fixture_used": False
        }
    }
