CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_live_evidence_source_planner():
    results = []
    for tk in CANDIDATES:
        sources = {
            "quote": {"primary": "Yahoo_Finance", "fallback": "Alpha_Vantage", "requires_free_tier": True, "no_login_required": True},
            "financial": {"primary": "SEC_EDGAR", "fallback": "FMP", "requires_free_tier": False, "no_login_required": True},
            "valuation": {"primary": "SEC_EDGAR", "fallback": "Yahoo_Finance", "requires_free_tier": True, "no_login_required": True, "derived_label_only": True},
            "news_event": {"primary": "Alpha_Vantage", "fallback": "MarketWatch", "requires_free_tier": True, "no_login_required": True},
            "filing_availability": {"primary": "SEC_EDGAR", "fallback": "Company_IR", "requires_free_tier": False, "no_login_required": True},
            "transcript_guidance": {"primary": "SEC_EDGAR", "fallback": "Company_IR", "requires_free_tier": False, "no_login_required": True}
        }
        results.append({
            "ticker": tk,
            "sources": sources,
            "all_sources_public": True,
            "all_sources_no_login": True,
            "no_bypass_login_required": True,
            "cannot_conclude": ["source_availability_is_not_source_success", "source_list_is_not_evidence_quality"]
        })
    return {
        "phase166_live_evidence_source_planner": {
            "total": len(results),
            "all_sources_public": True,
            "no_bypass_login_or_captcha": True,
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
