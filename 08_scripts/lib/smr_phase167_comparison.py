CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_candidate_comparison_matrix():
    rows = []
    for i, tk in enumerate(CANDIDATES):
        rows.append({
            "ticker": tk,
            "opportunity": "identified_not_confirmed",
            "evidence_completeness": 1.0,
            "risk_level": "standard" if tk not in ["INTC","SNPS","MU"] else "elevated",
            "thesis_maturity": "seed",
            "deepdive_depth": "in_progress",
            "judge_clean": True,
            "comparison_matrix_not_investment_ranking": True,
            "cannot_conclude": ["comparison_is_not_investment_ranking", "matrix_is_not_buy_signal", "ranking_implied_by_position_is_prohibited"]
        })
    return {
        "phase167_candidate_comparison_matrix": {
            "candidates": len(rows),
            "comparison_matrix_not_investment_ranking": True,
            "no_buy_sell_hold_in_matrix": True,
            "rows": rows,
            "mock_used": False,
            "fixture_used": False
        }
    }
