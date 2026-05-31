import json
from datetime import datetime

DIMENSIONS = [
    "financial_structured","financial_statements","price_daily","valuation",
    "pricing_expectation","industry_news","order_contract","customer_capex",
    "supply_chain","product_pricing","peer_benchmark","macro","sentiment",
    "filings_regulatory","management_guidance"
]

TICKERS = ["300308.SZ","688041.SH","002230.SZ","300394.SZ","09988.HK","00700.HK","NVDA","AVGO"]

# Coverage status per ticker per dimension: covered / partial / gap / blocked
DIM_COVERAGE = {
    "300308.SZ": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"covered","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "688041.SH": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"gap","pricing_expectation":"gap","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "002230.SZ": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"partial","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "300394.SZ": {
        "financial_structured":"blocked","financial_statements":"blocked","price_daily":"covered",
        "valuation":"blocked","pricing_expectation":"blocked","industry_news":"blocked",
        "order_contract":"blocked","customer_capex":"blocked","supply_chain":"blocked",
        "product_pricing":"blocked","peer_benchmark":"blocked","macro":"blocked",
        "sentiment":"blocked","filings_regulatory":"blocked","management_guidance":"blocked"
    },
    "09988.HK": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"covered","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "00700.HK": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"covered","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "NVDA": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"covered","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    },
    "AVGO": {
        "financial_structured":"covered","financial_statements":"covered","price_daily":"covered",
        "valuation":"covered","pricing_expectation":"covered","industry_news":"partial",
        "order_contract":"gap","customer_capex":"gap","supply_chain":"gap",
        "product_pricing":"gap","peer_benchmark":"partial","macro":"partial",
        "sentiment":"partial","filings_regulatory":"covered","management_guidance":"gap"
    }
}

def build_dimension_coverage_matrix():
    dim_rows = []
    dim_summary = {}
    
    for dim in DIMENSIONS:
        counts = {"covered":0,"partial":0,"gap":0,"blocked":0}
        ticker_statuses = {}
        for t in TICKERS:
            status = DIM_COVERAGE.get(t,{}).get(dim,"unknown")
            counts[status] = counts.get(status,0) + 1
            ticker_statuses[t] = status
        dim_summary[dim] = counts
        dim_rows.append({
            "dimension": dim,
            "coverage": counts,
            "ticker_detail": ticker_statuses
        })
    
    # Hard data gap report: focus on dimensions with gap > 0
    gap_report = []
    for dim in DIMENSIONS:
        counts = dim_summary.get(dim,{})
        if counts.get("gap",0) > 0 or counts.get("blocked",0) > 0:
            gap_tickers = [t for t in TICKERS if DIM_COVERAGE.get(t,{}).get(dim) in ("gap","blocked")]
            gap_report.append({
                "dimension": dim,
                "gap_count": counts.get("gap",0),
                "blocked_count": counts.get("blocked",0),
                "affected_tickers": gap_tickers,
                "gap_type": _classify_gap(dim),
                "priority_for_phase92_96": _gap_priority(dim)
            })
    
    return {
        "phase91_information_dimension_coverage_matrix": {
            "generated_at": datetime.now().isoformat(),
            "dimensions_audited": len(DIMENSIONS),
            "dimension_coverage": dim_rows,
            "dimension_summary": dim_summary
        },
        "phase91_hard_data_gap_report": {
            "generated_at": datetime.now().isoformat(),
            "total_gaps": sum(1 for r in gap_report),
            "gaps": gap_report
        }
    }

def _classify_gap(dim):
    mapping = {
        "order_contract":"no_order_contract_bid_win_source",
        "customer_capex":"no_customer_capex_procurement_source",
        "supply_chain":"no_supply_chain_capacity_delivery_source",
        "product_pricing":"no_product_ASP_supply_demand_source",
        "management_guidance":"no_management_guidance_proxy_source",
        "pricing_expectation":"pricing_data_source_gap",
        "valuation":"valuation_data_source_gap"
    }
    return mapping.get(dim, f"{dim}_source_gap")

def _gap_priority(dim):
    priority = {
        "order_contract":"highest","customer_capex":"highest","supply_chain":"highest",
        "product_pricing":"high","management_guidance":"high",
        "pricing_expectation":"medium","valuation":"medium",
        "industry_news":"medium","sentiment":"low","macro":"low"
    }
    return priority.get(dim, "medium")
