"""
Phase 143: Cross Link Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline


def extract_cross_link_result(r):
    """
    从 build 结果中提取交叉链接的关键数据
    
    Args:
        r: build_phase143_cross_link_dashboard 的返回值
    
    Returns:
        包含交叉链接关键指标的字典
    """
    dash = r["phase143_cross_link_dashboard"]
    return {
        "site_map_pages": dash["site_map"]["pages"],
        "link_integrity": dash["link_integrity"]["overall_status"],
        "files_checked": dash["link_integrity"]["files_checked"],
        "files_pass": dash["link_integrity"]["files_pass"],
        "quality_gate": dash["quality_gate"]["overall_status"],
        "guard": dash["guard"]["overall_status"],
        "violations": dash["guard"]["violations"],
        "static_html_only": True,
        "external_js_allowed": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
    }


run_phase143_cross_link_pipeline = create_pipeline(
    phase_num=143,
    build_module="build_phase143_cross_link_dashboard",
    result_extractor=extract_cross_link_result,
    output_name="phase143_cross_link_pipeline"
)

# Backward-compatible public entry point retained for the phase runner tests and
# any local automation written before the descriptive function name was added.
def run_pipeline(mode="dry-run"):
    return run_phase143_cross_link_pipeline([f"--{mode}"])


if __name__ == "__main__":
    run_phase143_cross_link_pipeline()
