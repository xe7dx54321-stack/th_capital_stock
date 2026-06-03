import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

from smr_phase143_config import load_phase143_config
from smr_phase143_site_map_builder import build_site_map
from smr_phase143_link_integrity_checker import check_link_integrity
from smr_phase143_navigation_css import build_navigation_css
from smr_phase143_quality_gate import run_phase143_quality_gate
from smr_phase143_guard import run_phase143_guard
from smr_phase143_backlog import build_phase143_backlog


def build():
    cfg = load_phase143_config()
    site_map = build_site_map()
    ROOT = Path(__file__).resolve().parent.parent.parent
    integrity = check_link_integrity(str(ROOT / "09_runbooks" / "generated"))
    nav_css = build_navigation_css()
    quality = run_phase143_quality_gate(integrity)
    guard = run_phase143_guard()
    backlog = build_phase143_backlog()

    return {
        "phase143_cross_link_dashboard": {
            "config": cfg,
            "site_map": site_map["phase143_site_map"],
            "link_integrity": integrity["phase143_link_integrity_check"],
            "navigation_css": nav_css["phase143_navigation_css"]["ready"],
            "quality_gate": quality["phase143_quality_gate"],
            "guard": guard["phase143_cannot_conclude_guard"],
            "backlog": backlog["phase143_backlog"],
            "static_html_only": True,
            "external_js_allowed": False,
            "mock_used": False,
            "fixture_used": False,
            "trade_recommendation_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0,
            "paper_order_created": 0,
        }
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
