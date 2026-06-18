"""
Phase 153: Onboarding Review Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_onboarding_result(r):
    """
    从 build 结果中提取入池审查的关键数据
    
    Args:
        r: build_phase153_onboarding_review_dashboard 的返回值
    
    Returns:
        包含入池审查关键指标的字典
    """
    d = r["phase153_onboarding_review_dashboard"]
    b = d["board"]
    js = b["judge_summary"]
    return {
        "candidates_reviewed": b["candidates_reviewed"],
        "ready_for_owner_approval": js.get("ready_for_owner_approval", 0),
        "needs_evidence_agent_follow_up": js.get("needs_evidence_agent_follow_up", 0),
        "needs_identity_confirmation": js.get("needs_identity_confirmation", 0),
        "blocked_for_now": js.get("blocked_for_now", 0),
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "activation_allowed": False,
        "auto_add_to_watchlist_allowed": False,
        "auto_promote_to_core_allowed": False,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "judge_pass_not_investment_approval": True,
        "onboarding_review_not_watch_activation": True,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase153_onboarding_review_pipeline = create_pipeline(
    phase_num=153,
    build_module="build_phase153_onboarding_review_dashboard",
    result_extractor=extract_onboarding_result,
    output_name="phase153_onboarding_review_pipeline"
)


if __name__ == "__main__":
    run_phase153_onboarding_review_pipeline()
