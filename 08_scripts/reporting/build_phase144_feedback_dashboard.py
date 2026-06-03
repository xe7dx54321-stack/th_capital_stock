import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

from smr_phase144_config import load_phase144_config
from smr_phase144_feedback_form_builder import build_feedback_forms
from smr_phase144_ticker_checklist_builder import build_ticker_checklists
from smr_phase144_feedback_html_section import build_feedback_html_section
from smr_phase144_quality_gate import run_phase144_quality_gate
from smr_phase144_guard import run_phase144_guard
from smr_phase144_backlog import build_phase144_backlog


def build():
    cfg = load_phase144_config()
    forms = build_feedback_forms()
    checklists = build_ticker_checklists()
    html_section = build_feedback_html_section()
    quality = run_phase144_quality_gate()
    guard = run_phase144_guard()
    backlog = build_phase144_backlog()

    return {
        "phase144_feedback_dashboard": {
            "config": cfg,
            "feedback_forms": forms["phase144_feedback_forms"],
            "ticker_checklists": checklists["phase144_ticker_checklists"],
            "html_section_ready": len(html_section["phase144_feedback_html_section"]["html"]) > 100,
            "quality_gate": quality["phase144_quality_gate"],
            "guard": guard["phase144_cannot_conclude_guard"],
            "backlog": backlog["phase144_backlog"],
            "static_html_only": True,
            "external_js_allowed": False,
            "mock_used": False, "fixture_used": False,
            "trade_recommendation_created": 0,
            "target_price_created": 0,
            "paper_order_created": 0,
        }
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
