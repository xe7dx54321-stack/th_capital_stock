"""
Phase 152: Admission Scoring Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_admission_result(r):
    """
    从 build 结果中提取入池评分的关键数据
    
    Args:
        r: build_phase152_admission_scoring_dashboard 的返回值
    
    Returns:
        包含入池评分关键指标的字典
    """
    d = r["phase152_admission_scoring_dashboard"]
    board = d["board"]
    bsum = board["buckets"]
    return {
        "scored_candidates": board["scored_candidates"],
        "admit_to_onboarding_review": bsum.get("admit_to_onboarding_review", 0),
        "watch_for_more_evidence": bsum.get("watch_for_more_evidence", 0),
        "manual_identity_or_source_review": bsum.get("manual_identity_or_source_review", 0),
        "defer": bsum.get("defer", 0),
        "reject_for_now": bsum.get("reject_for_now", 0),
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "agent_routing": {
            "evidence_agent": d["agent_routing"]["evidence_agent"]["candidates_routed"],
            "risk_agent": d["agent_routing"]["risk_agent"]["candidates_routed"],
            "judge_agent": d["agent_routing"]["judge_agent"]["candidates_routed"],
        },
        "research_only": True,
        "auto_add_to_watchlist_allowed": False,
        "auto_promote_to_core_allowed": False,
        "admission_score_not_investment_rating": True,
        "admission_bucket_not_buy_sell": True,
        "trade_recommendation_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase152_admission_scoring_pipeline = create_pipeline(
    phase_num=152,
    build_module="build_phase152_admission_scoring_dashboard",
    result_extractor=extract_admission_result,
    output_name="phase152_admission_scoring_pipeline"
)


if __name__ == "__main__":
    run_phase152_admission_scoring_pipeline()
