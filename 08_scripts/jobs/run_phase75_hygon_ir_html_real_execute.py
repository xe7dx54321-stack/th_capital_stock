#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase74_hygon_ir_html_parser import parse_hygon_ir

def run(mode="execute", ticker="688041.SH"):
    sn = mode == "skip_network"
    network_attempted = mode == "execute"
    if mode == "dry_run":
        return {"phase75_hygon_ir_html_real_execute": {"mode": mode, "network_attempted": False,
            "ticker": ticker, "pages_checked": 0, "pages_fetched": 0, "text_blocks_found": 0,
            "texts_extracted": 0, "texts_usable": 0, "rows": [],
            "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    r = parse_hygon_ir(ticker, skip_network=sn)
    r["network_attempted"] = network_attempted
    r["mode"] = mode
    return {"phase75_hygon_ir_html_real_execute": r}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "dry_run" if getattr(a, "dry_run") else "execute"
    r = run(mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
