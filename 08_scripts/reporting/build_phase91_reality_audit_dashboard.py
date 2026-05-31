import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_source_inventory import build_source_inventory
from smr_phase91_source_reality_classifier import classify_sources
from smr_phase91_ticker_source_profile import build_ticker_source_profiles
from smr_phase91_dimension_coverage import build_dimension_coverage_matrix
from smr_phase91_depth_freshness_reliability_backlog import build_source_depth_scores, build_freshness_audit, build_reliability_crosscheck, build_backlog_priority

def main():
    inv=build_source_inventory()
    cls=classify_sources(inv)
    prof=build_ticker_source_profiles()
    dim=build_dimension_coverage_matrix()
    depth=build_source_depth_scores()
    fresh=build_freshness_audit()
    rel=build_reliability_crosscheck()
    bl=build_backlog_priority()
    
    cs=cls["phase91_source_reality_classifier"]["classification_summary"]
    gap=dim["phase91_hard_data_gap_report"]
    pr=prof["phase91_ticker_source_profile"]
    
    summary={
        "tickers_audited":8,
        "sources_inventoried":inv["phase91_existing_source_inventory"]["sources_inventoried"],
        "sources_classified":cls["phase91_source_reality_classifier"]["sources_classified"],
        "real_daily_source":cs.get("real_daily_source",0),
        "real_on_demand_source":cs.get("real_on_demand_source",0),
        "partial_real_source":cs.get("partial_real_source",0),
        "fallback_only_source":cs.get("fallback_only_source",0),
        "history_pool_source":cs.get("history_pool_source",0),
        "registry_only_source":cs.get("registry_only_source",0),
        "curated_catalog_source":cs.get("curated_catalog_source",0),
        "blocked_source":cs.get("blocked_source",0),
        "manual_required_source":cs.get("manual_required_source",0),
        "dimensions_audited":dim["phase91_information_dimension_coverage_matrix"]["dimensions_audited"],
        "hard_data_gaps":gap["total_gaps"],
        "reliability_gaps_found":rel["phase91_reliability_vs_reality_crosscheck"]["reliability_gaps_found"],
        "backlog_items":bl["phase91_source_backlog_priority"]["backlog_items"],
        "ticker_with_highest_depth":max(pr["profiles"],key=lambda x:x.get("source_depth_score",0)).get("ticker",""),
        "max_depth_score":max(p.get("source_depth_score",0) for p in pr["profiles"]),
        "average_depth_score":pr["average_source_depth_score"],
        "blocked_tickers":sum(1 for p in pr["profiles"] if p.get("blocked",False)),
        "phase92_96_recommendation":bl["phase91_source_backlog_priority"]["phase92_96_recommendation"],
        "audit_status":"complete",
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "target_price_created":0,"position_sizing_created":0,
        "research_framework_created":False
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    elif "--markdown" in sys.argv:
        print(f"# Phase 91 Information Source Reality Audit Dashboard\n")
        print(f"## Summary\n")
        print(f"- Sources inventoried: {summary['sources_inventoried']}")
        print(f"- Real daily: {summary['real_daily_source']}, Real on-demand: {summary['real_on_demand_source']}")
        print(f"- Partial: {summary['partial_real_source']}, Fallback: {summary['fallback_only_source']}")
        print(f"- History pool: {summary['history_pool_source']}, Registry-only: {summary['registry_only_source']}")
        print(f"- Curated catalog: {summary['curated_catalog_source']}, Blocked: {summary['blocked_source']}")
        print(f"- Dimensions audited: {summary['dimensions_audited']}, Hard data gaps: {summary['hard_data_gaps']}")
        print(f"- Reliability gaps: {summary['reliability_gaps_found']}")
        print(f"- Avg depth score: {summary['average_depth_score']}")
        print(f"- Phase92-96: {summary['phase92_96_recommendation']}")
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
