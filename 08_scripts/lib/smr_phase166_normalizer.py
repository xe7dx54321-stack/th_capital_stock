def build_live_evidence_normalizer(quote_fill, financial_fill, valuation_fill, news_fill, filing_fill, transcript_fill):
    raw_saved = False
    normalized = []
    for i, tk in enumerate(["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]):
        entry = {
            "ticker": tk,
            "currency": "USD",
            "quote_normalized": quote_fill["phase166_quote_evidence_fill"]["results"][i]["quote_filled"],
            "financial_normalized": financial_fill["phase166_financial_evidence_fill"]["results"][i]["financial_filled"],
            "valuation_normalized": valuation_fill["phase166_valuation_evidence_fill"]["results"][i]["valuation_filled"],
            "news_normalized": news_fill["phase166_news_event_evidence_fill"]["results"][i]["news_filled"],
            "filing_normalized": filing_fill["phase166_filing_evidence_availability"]["results"][i]["filing_checked"],
            "transcript_normalized": transcript_fill["phase166_transcript_guidance_evidence_availability"]["results"][i]["transcript_checked"],
            "raw_saved": raw_saved,
            "cannot_conclude": ["normalized_evidence_is_not_verified_evidence", "normalization_is_not_quality_approval"]
        }
        normalized.append(entry)
    return {
        "phase166_live_evidence_normalizer": {
            "candidates": len(normalized),
            "raw_saved": raw_saved,
            "raw_payload_not_saved": True,
            "results": normalized,
            "mock_used": False,
            "fixture_used": False
        }
    }
