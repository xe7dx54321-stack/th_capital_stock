import json, sys, os, argparse
from pathlib import Path
from datetime import datetime

BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))

from build_phase143_cross_link_dashboard import build


def run_pipeline(mode="dry-run"):
    started_at = datetime.now().isoformat()
    result = build()
    dash = result["phase143_cross_link_dashboard"]
    finished_at = datetime.now().isoformat()

    return {
        "phase143_cross_link_pipeline": {
            "mode": mode,
            "started_at": started_at,
            "finished_at": finished_at,
            "site_map_pages": dash["site_map"]["pages"],
            "link_integrity": dash["link_integrity"]["overall_status"],
            "files_checked": dash["link_integrity"]["files_checked"],
            "files_pass": dash["link_integrity"]["files_pass"],
            "quality_gate": dash["quality_gate"]["overall_status"],
            "guard": dash["guard"]["overall_status"],
            "violations": dash["guard"]["violations"],
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
