#!/usr/bin/env python3
"""Phase 71: Fallback text fetch job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", skip_network=False):
    if mode in ("dry_run", "dry-run"):
        return {"mode": "dry_run", "status": "dry_run"}
    from smr_irm_interaction_connector import build_irm_report
    from smr_exchange_disclosure_page_connector import build_exchange_report
    from smr_company_ir_page_discovery import build_company_ir_report
    from smr_fallback_text_fetcher import fetch_fallback_texts
    irm = build_irm_report()
    exc = build_exchange_report()
    cir = build_company_ir_report()
    return fetch_fallback_texts(irm, exc, cir)

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
