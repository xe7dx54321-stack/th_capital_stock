import os, sys, json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

from smr_phase142_config import load_phase142_config
from smr_phase142_domain_registry import build_phase142_domain_registry
from smr_phase142_ticker_detail_data_model import build_ticker_detail_data_model
from smr_phase142_ticker_detail_page_generator import generate_ticker_detail_page
from smr_phase142_detail_css_extension import build_detail_css_extension
from smr_phase142_ticker_detail_index_builder import build_ticker_detail_index
from smr_phase142_homepage_link_update_builder import build_homepage_link_update
from smr_phase142_detail_open_instruction import build_detail_open_instruction
from smr_phase142_detail_quality_gate import run_detail_quality_gate
from smr_phase142_detail_cannot_conclude_guard import run_detail_cannot_conclude_guard
from smr_phase142_detail_backlog_update import build_detail_backlog_update
from smr_phase142_phase141_dashboard_loader import load_phase141_dashboard_data
from smr_phase142_phase138_thesis_loader import load_phase138_thesis_data
from smr_phase142_phase137_deep_dive_loader import load_phase137_deep_dive_data
from smr_phase142_phase134_console_loader import load_phase134_console_data

def build():
    cfg = load_phase142_config()
    model = build_ticker_detail_data_model()
    css_ext = build_detail_css_extension()
    css = css_ext["phase142_detail_css_extension"]["css"]
    ticker_data = model["phase142_ticker_detail_data_model"]["ticker_data"]
    pages = {}
    for td in ticker_data:
        pages[td["ticker"]] = generate_ticker_detail_page(td, css)
    index_html = build_ticker_detail_index(ticker_data, css)
    quality = run_detail_quality_gate(pages)
    guard = run_detail_cannot_conclude_guard()
    domain = build_phase142_domain_registry()
    links = build_homepage_link_update()
    instr = build_detail_open_instruction()
    backlog = build_detail_backlog_update()
    ph141 = load_phase141_dashboard_data()
    out = {
        "detail_pages_count": len(pages),
        "detail_index_generated": len(index_html) > 100,
        "quality_gate": quality["phase142_detail_quality_gate"]["overall_status"],
        "cannot_conclude_guard": guard["phase142_detail_cannot_conclude_guard"]["overall_status"],
        "violations": guard["phase142_detail_cannot_conclude_guard"]["violations"],
        "homepage_links": links["phase142_homepage_link_update"]["links"],
        "static_html_only": True,
        "external_js_allowed": False,
        "external_cdn_allowed": False,
        "mock_used": False,
        "fixture_used": False,
        "trade_recommendation_created": 0,
        "target_price_created": 0,
        "position_sizing_created": 0,
        "paper_order_created": 0,
        "paper_trade_created": 0,
        "broker_api_called": False
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    build()
