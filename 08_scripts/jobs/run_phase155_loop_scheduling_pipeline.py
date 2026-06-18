"""
Phase 155: Loop Scheduling Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_scheduling_result(r):
    """
    从 build 结果中提取调度循环的关键数据
    
    Args:
        r: build_phase155_scheduling_dashboard 的返回值
    
    Returns:
        包含调度循环关键指标的字典
    """
    d = r["phase155_scheduling_dashboard"]
    b = d["board"]
    return {
        "daily_targets": b["loop_plan"]["daily"]["targets_count"],
        "weekly_targets": b["loop_plan"]["weekly"]["weekly_targets_total"],
        "event_triggers": b["loop_plan"]["event"]["triggers"],
        "history_is_first_run": b["loop_history"]["reader"]["is_first_run"],
        "delta_available": b["loop_history"]["delta"]["delta_available"],
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True,
        "agent_simulation_only": True,
        "live_llm_call_made": False,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "schedule_not_trade_plan": True,
        "event_not_trade_signal": True,
        "history_not_pnl": True,
        "digest_not_advice": True,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False,
        "llm_api_called": False,
    }


run_phase155_loop_scheduling_pipeline = create_pipeline(
    phase_num=155,
    build_module="build_phase155_scheduling_dashboard",
    result_extractor=extract_scheduling_result,
    output_name="phase155_loop_scheduling_pipeline"
)


if __name__ == "__main__":
    run_phase155_loop_scheduling_pipeline()
