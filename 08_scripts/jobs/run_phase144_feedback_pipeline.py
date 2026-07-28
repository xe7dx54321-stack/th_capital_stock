"""
Phase 144: Feedback Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_feedback_result(r):
    """
    从 build 结果中提取反馈 pipeline 的关键数据
    
    Args:
        r: build_phase144_feedback_dashboard 的返回值
    
    Returns:
        包含反馈关键指标的字典
    """
    dash = r["phase144_feedback_dashboard"]
    return {
        "forms_defined": dash["feedback_forms"]["forms"],
        "ticker_checklists": dash["ticker_checklists"]["tickers"],
        "html_section_ready": dash["html_section_ready"],
        "quality_gate": dash["quality_gate"]["overall_status"],
        "guard": dash["guard"]["overall_status"],
        "violations": dash["guard"]["violations"],
        "static_html_only": True,
        "external_js_allowed": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "paper_order_created": 0,
    }


run_phase144_feedback_pipeline = create_pipeline(
    phase_num=144,
    build_module="build_phase144_feedback_dashboard",
    result_extractor=extract_feedback_result,
    output_name="phase144_feedback_pipeline"
)

# Preserve the original runner contract used by existing local automation.
def run_pipeline(mode="dry-run"):
    return run_phase144_feedback_pipeline([f"--{mode}"])


if __name__ == "__main__":
    run_phase144_feedback_pipeline()
