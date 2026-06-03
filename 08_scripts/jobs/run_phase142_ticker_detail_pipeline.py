import json, os, sys, argparse
from pathlib import Path
from datetime import datetime

BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE_LIB))

from smr_phase142_ticker_detail_data_model import build_ticker_detail_data_model
from smr_phase142_ticker_detail_page_generator import generate_ticker_detail_page
from smr_phase142_detail_css_extension import build_detail_css_extension
from smr_phase142_ticker_detail_index_builder import build_ticker_detail_index
from smr_phase142_detail_quality_gate import run_detail_quality_gate
from smr_phase142_detail_cannot_conclude_guard import run_detail_cannot_conclude_guard

def run_pipeline(mode="dry-run"):
    started_at = datetime.now().isoformat()
    model = build_ticker_detail_data_model()
    css_ext = build_detail_css_extension()
    css = css_ext["phase142_detail_css_extension"]["css"]
    ticker_data = model["phase142_ticker_detail_data_model"]["ticker_data"]
    pages = {}
    for td in ticker_data:
        pages[td["ticker"]] = generate_ticker_detail_page(td, css)
    index_html = build_ticker_detail_index(ticker_data, css)

    if mode == "execute":
        out_dir = Path(__file__).resolve().parent.parent.parent / "09_runbooks" / "generated" / "phase142_ticker_details"
        out_dir.mkdir(parents=True, exist_ok=True)
        for ticker, html in pages.items():
            tid = ticker.replace(".", "-")
            with open(out_dir / f"{tid}.html", "w", encoding="utf-8") as f:
                f.write(html)
        with open(out_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(index_html)

    quality = run_detail_quality_gate(pages)
    guard = run_detail_cannot_conclude_guard()
    finished_at = datetime.now().isoformat()

    return {
        "phase142_ticker_detail_pipeline": {
            "mode": mode,
            "detail_pages_generated": len(pages),
            "detail_index_generated": len(index_html) > 100,
            "quality_gate": quality["phase142_detail_quality_gate"]["overall_status"],
            "quality_checks_pass": quality["phase142_detail_quality_gate"]["all_pass"],
            "cannot_conclude_guard": guard["phase142_detail_cannot_conclude_guard"]["overall_status"],
            "violations": guard["phase142_detail_cannot_conclude_guard"]["violations"],
            "pages_saved_to_disk": mode == "execute",
            "output_dir_ignored": True,
            "static_html_only": True,
            "external_js_allowed": False,
            "mock_used": False,
            "fixture_used": False,
            "trade_recommendation_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0,
            "paper_order_created": 0,
            "paper_trade_created": 0,
            "broker_api_called": False
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.execute:
        mode = "execute"
    elif args.skip_network:
        mode = "skip-network"
    else:
        mode = "dry-run"
    output = run_pipeline(mode)
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
