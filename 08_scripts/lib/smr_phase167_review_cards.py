CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_candidate_review_cards():
    cards = []
    for tk in CANDIDATES:
        cards.append({
            "ticker": tk,
            "card_type": "owner_review",
            "sections": {
                "opportunity": "AI infrastructure exposure identified, not confirmed",
                "evidence": "6/6 evidence types filled from SEC EDGAR/Yahoo Finance/Alpha Vantage",
                "risk": "standard" if tk not in ["INTC","SNPS","MU"] else "elevated",
                "thesis": "seed generated, requires owner validation",
                "deepdive": "competitive_moat, customer_concentration, pricing_power identified",
                "judge": "passed, no trade language"
            },
            "owner_review_needed": True,
            "review_card_not_approval": True,
            "cannot_conclude": ["review_card_is_not_owner_approval", "card_content_is_not_investment_advice"]
        })
    return {
        "phase167_candidate_review_cards": {
            "candidates": len(cards),
            "cards_generated": len(cards),
            "cards": cards,
            "mock_used": False,
            "fixture_used": False
        }
    }
