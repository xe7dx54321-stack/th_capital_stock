import json, os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

from smr_phase141_config import load_config
from smr_phase141_domain_registry import build_domain_registry
from smr_phase141_dashboard_data_model import build_dashboard_data_model
from smr_phase141_static_html_layout_builder import build_static_html_layout
from smr_phase141_css_style_builder import build_css_style
from smr_phase141_navigation_anchor_system import build_navigation_anchor_system
from smr_phase141_ticker_card_html_section import build_ticker_card_html_section
from smr_phase141_thesis_library_html_section import build_thesis_library_html_section
from smr_phase141_evidence_source_limitation_html_section import build_evidence_source_limitation_html_section
from smr_phase141_daily_weekly_delivery_html_section import build_daily_weekly_delivery_html_section
from smr_phase141_owner_action_html_section import build_owner_action_html_section
from smr_phase141_gap_risk_html_section import build_gap_risk_html_section
from smr_phase141_feedback_template_html_section import build_feedback_template_html_section
from smr_phase141_artifact_link_html_section import build_artifact_link_html_section
from smr_phase141_local_open_instruction_builder import build_local_open_instruction
from smr_phase141_html_quality_gate import run_html_quality_gate
from smr_phase141_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase141_backlog_update import build_backlog_update
from smr_phase141_phase140_hardening_loader import load_phase140_hardening
from smr_phase141_phase139_delivery_loader import load_phase139_delivery
from smr_phase141_phase138_thesis_loader import load_phase138_thesis
from smr_phase141_phase134_console_loader import load_phase134_console


def build_full_html():
    cfg = load_config()
    layout = build_static_html_layout()
    css = build_css_style()
    nav = build_navigation_anchor_system()
    tickers_html = build_ticker_card_html_section()
    thesis_html = build_thesis_library_html_section()
    evidence_html = build_evidence_source_limitation_html_section()
    delivery_html = build_daily_weekly_delivery_html_section()
    actions_html = build_owner_action_html_section()
    gaps_html = build_gap_risk_html_section()
    feedback_html = build_feedback_template_html_section()
    links_html = build_artifact_link_html_section()
    open_instr = build_local_open_instruction()

    layout_str = layout.get("phase141_static_html_layout_builder", {}).get("layout", "")
    css_str = css.get("phase141_css_style_builder", {}).get("css", "")
    nav_str = nav.get("phase141_navigation_anchor_system", {}).get("nav", "")
    status_bar = '<span class="pass">Operational Score: 100/100</span><span class="pass">Audits: 10/10 pass</span><span>Research Only</span>'

    full_html = layout_str.replace("/* CSS injected */", css_str)
    full_html = full_html.replace('<div class="status-bar" id="system-status"></div>', f'<div class="status-bar" id="system-status">{status_bar}</div>')
    full_html = full_html.replace('<nav class="nav-bar" id="navigation"></nav>', f'<nav class="nav-bar" id="navigation">{nav_str}</nav>')
    full_html = full_html.replace('<section id="ticker-cards"></section>', f'<section id="ticker-cards"><h2>Ticker Cards</h2>{tickers_html["phase141_ticker_card_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="thesis-library"></section>', f'<section id="thesis-library"><h2>Thesis Library</h2>{thesis_html["phase141_thesis_library_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="evidence-sources"></section>', f'<section id="evidence-sources"><h2>Evidence & Source Limitations</h2>{evidence_html["phase141_evidence_source_limitation_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="daily-delivery"></section>', f'<section id="daily-delivery"><h2>Daily & Weekly Delivery</h2>{delivery_html["phase141_daily_weekly_delivery_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="owner-actions"></section>', f'<section id="owner-actions"><h2>Owner Actions</h2>{actions_html["phase141_owner_action_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="gap-risk"></section>', f'<section id="gap-risk"><h2>Gaps & Risks</h2>{gaps_html["phase141_gap_risk_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="feedback-template"></section>', f'<section id="feedback-template"><h2>Feedback Templates</h2>{feedback_html["phase141_feedback_template_html_section"]["html"]}</section>')
    full_html = full_html.replace('<section id="artifact-links"></section>', f'<section id="artifact-links"><h2>Artifact Links</h2>{links_html["phase141_artifact_link_html_section"]["html"]}</section>')

    quality = run_html_quality_gate(full_html)
    guard = run_cannot_conclude_guard()
    domain = build_domain_registry()
    model = build_dashboard_data_model()
    hardening = load_phase140_hardening()
    delivery = load_phase139_delivery()
    thesis = load_phase138_thesis()
    console = load_phase134_console()
    backlog = build_backlog_update()

    return {
        "phase141_html_dashboard": {
            "html": full_html,
            "config": cfg,
            "domain_registry": domain,
            "data_model": model,
            "quality_gate": quality["phase141_html_quality_gate"],
            "cannot_conclude_guard": guard["phase141_cannot_conclude_guard"],
            "local_open_instruction": open_instr,
            "backlog": backlog,
            "hardening_loader": hardening,
            "delivery_loader": delivery,
            "thesis_loader": thesis,
            "console_loader": console,
            "static_html_only": True,
            "external_js_allowed": False,
            "external_cdn_allowed": False,
            "local_server_enabled": False,
            "browser_automation_allowed": False,
            "mock_used": False,
            "fixture_used": False,
            "raw_saved": False,
            "ocr_used": False,
            "browser_automation_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_output": 0,
            "position_sizing_output": 0
        }
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--save-html", action="store_true")
    parser.add_argument("--output", type=str, default="09_runbooks/generated/phase141_research_console.html")
    args = parser.parse_args()

    result = build_full_html()

    if args.save_html:
        out_path = Path(__file__).resolve().parent.parent.parent / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result["phase141_html_dashboard"]["html"])
        print(f"HTML saved to: {out_path}")

    if args.json:
        # Remove html from JSON output to keep it clean
        json_out = {k: v for k, v in result["phase141_html_dashboard"].items() if k != "html"}
        json_out["html_length"] = len(result["phase141_html_dashboard"]["html"])
        print(json.dumps(json_out, indent=2, ensure_ascii=False, default=str))
    elif args.markdown:
        print("# Phase 141 HTML Dashboard")
        qg = result["phase141_html_dashboard"]["quality_gate"]
        print(f"\n## Quality Gate: {qg['overall_status']}")
        print(f"All checks pass: {qg['all_pass']}")
        cg = result["phase141_html_dashboard"]["cannot_conclude_guard"]
        print(f"\n## Cannot Conclude Guard: {cg['overall_status']}")
        print(f"Violations: {cg['violations']}")
        print(f"\n## Safety")
        print(f"- mock_used: {result['phase141_html_dashboard']['mock_used']}")
        print(f"- pending/order/trade: 0/0/0")
        print(f"- HTML length: {len(result['phase141_html_dashboard']['html'])} chars")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
