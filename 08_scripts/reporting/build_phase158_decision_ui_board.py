import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase158_loaders import load_pending_candidates
    from smr_phase158_ui_data_model import build_decision_ui_data_model
    from smr_phase158_decision_card import build_decision_cards
    from smr_phase158_decision_options import build_allowed_decision_options
    from smr_phase158_template_renderer import render_decision_template_json
    from smr_phase158_markdown_guide import build_markdown_fill_guide
    from smr_phase158_validation_preview import build_validation_preview
    from smr_phase158_simulation_preview import build_simulation_preview
    from smr_phase158_rollback_explanation import build_rollback_explanation
    from smr_phase158_console_section import build_console_section_html
    from smr_phase158_console_page import build_console_page_html
    from smr_phase158_nav_integration import build_nav_integration
    from smr_phase158_css_extension import build_css_extension
    from smr_phase158_export_instructions import build_export_instructions
    from smr_phase158_import_instructions import build_import_instructions
    from smr_phase158_link_checker import check_ui_links
    from smr_phase158_ui_safety_copy import check_ui_safety_copy

    candidates = load_pending_candidates()
    ui_model = build_decision_ui_data_model(candidates)
    cards = build_decision_cards(ui_model["phase158_ui_data_model"])
    options = build_allowed_decision_options()
    template = render_decision_template_json(candidates)
    guide = build_markdown_fill_guide()
    val_preview = build_validation_preview()
    sim_preview = build_simulation_preview()
    rollback = build_rollback_explanation()
    section = build_console_section_html()
    page = build_console_page_html()
    nav = build_nav_integration()
    css = build_css_extension()
    export_inst = build_export_instructions()
    import_inst = build_import_instructions()
    links = check_ui_links()
    safety = check_ui_safety_copy()

    return {"phase158_decision_ui_board":{
        "ui_data_model":ui_model["phase158_ui_data_model"],
        "decision_cards":cards["phase158_decision_cards"],
        "decision_options":options["phase158_decision_options"],
        "template_renderer":template["phase158_template_renderer"],
        "markdown_guide":guide["phase158_markdown_guide"],
        "validation_preview":val_preview["phase158_validation_preview"],
        "simulation_preview":sim_preview["phase158_simulation_preview"],
        "rollback":rollback["phase158_rollback_explanation"],
        "console_section":section["phase158_console_section"],
        "console_page":page["phase158_console_page"],
        "nav_integration":nav["phase158_nav_integration"],
        "css_extension":css["phase158_css_extension"],
        "export_instructions":export_inst["phase158_export_instructions"],
        "import_instructions":import_inst["phase158_import_instructions"],
        "link_checker":links["phase158_link_checker"],
        "ui_safety_copy":safety["phase158_ui_safety_copy"],
        "static_html_only":True,"execution_blocked":True,"trade_buttons_disabled":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
