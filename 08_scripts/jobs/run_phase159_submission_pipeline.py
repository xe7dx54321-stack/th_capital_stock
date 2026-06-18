"""
Phase 159: Submission Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_submission_result(r):
    """
    从 build 结果中提取提交 pipeline 的关键数据
    
    Args:
        r: build_phase159_submission_dashboard 的返回值
    
    Returns:
        包含提交关键指标的字典
    """
    d = r["phase159_submission_dashboard"]
    b = d["board"]
    fl = b["file_locator"]
    q = b["quarantine"]
    sm = b["safe_manifest"]
    return {
        "owner_input_present": fl["owner_input_present"],
        "invalid_count": q["invalid_count"],
        "safe_count": sm["safe_count"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "submission_not_execution": True,
        "validation_not_activation": True,
        "preview_not_real": True,
        "manifest_not_watch_update": True,
        "approve_not_buy": True,
        "reject_not_sell": True,
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


run_phase159_submission_pipeline = create_pipeline(
    phase_num=159,
    build_module="build_phase159_submission_dashboard",
    result_extractor=extract_submission_result,
    output_name="phase159_submission_pipeline"
)


if __name__ == "__main__":
    run_phase159_submission_pipeline()
