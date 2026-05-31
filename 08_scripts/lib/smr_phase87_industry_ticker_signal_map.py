from smr_phase87_config import get_industry_directions,get_universe,get_signal_types
def build_industry_ticker_signal_map():
    directions=get_industry_directions();universe=get_universe();mapping=[]
    for d in directions:
        for t in d["tickers"]:
            if t not in universe:continue
            mkt="CN_A" if t.endswith(".SZ") or t.endswith(".SH") else ("HK" if t.endswith(".HK") else "US")
            mkt_sources=[];reliability=0.6
            if mkt=="CN_A":mkt_sources=["eastmoney_news_search","existing_disclosure_text_pool","exchange_announcement_cninfo","existing_pdf_text_pool","curated_keyword_catalog"];reliability=0.70
            elif mkt=="HK":mkt_sources=["yfinance_news","company_ir_page_known_url","existing_pdf_text_pool","public_industry_news_rss","curated_keyword_catalog"];reliability=0.60
            else:mkt_sources=["yfinance_news","company_ir_page_known_url","existing_pdf_text_pool","public_industry_news_rss","government_policy_page","curated_keyword_catalog"];reliability=0.65
            mapping.append({"ticker":t,"market":mkt,"industry_direction":d["id"],"direction_label":d["label"],"relevant_keywords":d["keywords"][:5],"mapped_sources":mkt_sources,"source_count":len(mkt_sources),"avg_source_reliability":reliability})
    return {"phase87_industry_ticker_signal_map":{"tickers_mapped":len(universe),"industry_directions":len(directions),"mappings":len(mapping),"rows":mapping,"mock_used":False,"fixture_used":False}}
