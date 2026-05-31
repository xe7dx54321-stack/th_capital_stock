import json
from datetime import datetime

UNIVERSE = ["300308.SZ","688041.SH","002230.SZ","300394.SZ","09988.HK","00700.HK","NVDA","AVGO"]

TICKER_PROFILES = {
    "300308.SZ": {
        "ticker":"300308.SZ","market":"CN_A","company":"Zhongji Innolight",
        "profile_status":"partially_covered",
        "source_depth_score": 6,
        "available_sources": ["akshare_sina_financial","eastmoney_price","phase85_cn_valuation","phase86_expectation","phase86_pricing","phase87_external"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data","product_pricing_data","management_guidance_data"],
        "hard_data_gaps": ["no_order_book_visibility","no_customer_capex_breakdown","no_real_time_supply_chain","no_product_ASP_data"],
        "blocked": False
    },
    "688041.SH": {
        "ticker":"688041.SH","market":"CN_A","company":"Hygon Information",
        "profile_status":"partially_covered_with_gaps",
        "source_depth_score": 5,
        "available_sources": ["akshare_sina_financial","eastmoney_price","phase85_cn_valuation","phase86_expectation","phase87_external"],
        "missing_sources": ["pricing_data","order_contract_data","customer_capex_data","supply_chain_data","product_pricing_data","management_guidance_data"],
        "hard_data_gaps": ["pricing_unavailable","valuation_gap_persists","no_order_visibility","no_customer_breakdown"],
        "blocked": False,
        "known_gaps": ["pricing_unavailable","valuation_unavailable"]
    },
    "002230.SZ": {
        "ticker":"002230.SZ","market":"CN_A","company":"iFlytek",
        "profile_status":"partially_covered",
        "source_depth_score": 5,
        "available_sources": ["akshare_sina_financial","eastmoney_price","phase85_cn_valuation","phase86_expectation","phase87_external"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data","product_pricing_data","management_guidance_data"],
        "hard_data_gaps": ["no_order_book_visibility","no_government_contract_data","no_enterprise_customer_breakdown"],
        "blocked": False
    },
    "300394.SZ": {
        "ticker":"300394.SZ","market":"CN_A","company":"Tianfu Communication",
        "profile_status":"blocked",
        "source_depth_score": 0,
        "available_sources": [],
        "missing_sources": ["cninfo_org_id_missing","all_structured_financial_blocked","all_disclosure_blocked"],
        "hard_data_gaps": ["complete_financial_blackout","no_structured_data_available"],
        "blocked": True,
        "blocker": "cninfo_org_id_missing_and_known_url_not_usable",
        "allowed_next_action": "manual_cninfo_identity_resolution_or_alternative_source"
    },
    "09988.HK": {
        "ticker":"09988.HK","market":"HK","company":"Alibaba Group",
        "profile_status":"covered",
        "source_depth_score": 7,
        "available_sources": ["akshare_hk_financial","yfinance_financials","yfinance_price","phase85_hk_valuation","phase86_expectation","phase86_pricing","phase87_external"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data","product_pricing_data"],
        "hard_data_gaps": ["no_order_book_visibility","no_cloud_customer_breakdown","no_logistics_supply_chain_data"],
        "blocked": False
    },
    "00700.HK": {
        "ticker":"00700.HK","market":"HK","company":"Tencent Holdings",
        "profile_status":"covered",
        "source_depth_score": 7,
        "available_sources": ["akshare_hk_financial","yfinance_financials","yfinance_price","phase85_hk_valuation","phase86_expectation","phase86_pricing","phase87_external"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data","product_pricing_data"],
        "hard_data_gaps": ["no_order_book_visibility","no_game_pipeline_breakdown","no_ad_revenue_by_vertical"],
        "blocked": False
    },
    "NVDA": {
        "ticker":"NVDA","market":"US","company":"NVIDIA",
        "profile_status":"covered",
        "source_depth_score": 8,
        "available_sources": ["yfinance_financials","yfinance_price","sec_edgar","phase85_us_valuation","phase86_expectation","phase86_pricing","phase87_external","phase88_connector"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data"],
        "hard_data_gaps": ["no_customer_capex_breakdown","no_supply_chain_visibility","no_per_customer_revenue"],
        "blocked": False
    },
    "AVGO": {
        "ticker":"AVGO","market":"US","company":"Broadcom",
        "profile_status":"covered",
        "source_depth_score": 7,
        "available_sources": ["yfinance_financials","yfinance_price","sec_edgar","phase85_us_valuation","phase86_expectation","phase86_pricing","phase87_external","phase88_connector"],
        "missing_sources": ["order_contract_data","customer_capex_data","supply_chain_data"],
        "hard_data_gaps": ["no_customer_capex_breakdown","no_supply_chain_visibility","no_per_customer_revenue"],
        "blocked": False
    }
}

def build_ticker_source_profiles():
    profiles = []
    for t in UNIVERSE:
        p = TICKER_PROFILES.get(t, {"ticker":t,"profile_status":"unknown","source_depth_score":0,"blocked":False})
        profiles.append(p)
    
    avg_depth = sum(p.get("source_depth_score",0) for p in profiles) / len(profiles) if profiles else 0
    
    return {
        "phase91_ticker_source_profile": {
            "generated_at": datetime.now().isoformat(),
            "tickers_profiled": len(profiles),
            "average_source_depth_score": round(avg_depth, 1),
            "profiles": profiles
        }
    }
