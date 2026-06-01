import json,os
def build_field_missingness_report(records):
    """Report which fields are missing for which tickers."""
    from smr_phase96_config import get_universe, get_hard_data_categories
    universe=get_universe();categories=get_hard_data_categories()
    critical_missing=[]
    ticker_cat_map={}
    for r in records:
        t=r["ticker"];c=r["hard_data_category"]
        ticker_cat_map.setdefault(t,set()).add(c)
    for t in universe:
        covered=ticker_cat_map.get(t,set())
        missing=[c for c in categories if c not in covered]
        if missing:
            critical_missing.append({"ticker":t,"missing_categories":missing,"missing_count":len(missing),"severity":"critical" if len(missing)>=4 else "moderate"})
    return {"phase96_field_missingness_report":{"total_missing_fields":sum(m["missing_count"] for m in critical_missing),"critical_missing_fields":len(critical_missing),"rows":critical_missing,"mock_used":False,"fixture_used":False}}
