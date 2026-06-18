"""
Phase 156: Activation Review Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_activation_review_result(r):
    """
    从 build 结果中提取激活审查的关键数据
    
    Args:
        r: build_phase156_activation_dashboard 的返回值
    
    Returns:
        包含激活审查关键指标的字典
    """
    d = r["phase156_activation_dashboard"]
    b = d["board"]
    dc = b["decision_classifier"]
    cs = dc["summary"]
    return {
        "candidates_for_review": dc["total"],
        "pending_owner_review": cs["pending_owner_review"],
        "approved": cs["approved"],
        "deferred": cs["deferred"],
        "rejected": cs["rejected"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "owner_decision_required": True,
        "auto_approval_allowed": False,
        "owner_approval_not_trade_approval": True,
        "approve_not_equal_to_buy": True,
        "reject_not_equal_to_sell": True,
        "activation_queue_not_watchlist": True,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase156_activation_review_pipeline = create_pipeline(
    phase_num=156,
    build_module="build_phase156_activation_dashboard",
    result_extractor=extract_activation_review_result,
    output_name="phase156_activation_review_pipeline"
)


if __name__ == "__main__":
    run_phase156_activation_review_pipeline()
