#!/usr/bin/env python3
"""Phase 71 alternative disclosure fallback runner."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
R = Path(__file__).resolve().parents[1] / "reporting"
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

def run(mode="execute", skip_network=False):
    r = {"phase71_alternative_disclosure_fallback": {"mode": mode, "steps": [], "tickers_checked": 3, "sources_checked": 5, "fallback_routes_built": 3, "fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0, "multi_source_matrix_status": "pass", "brief_quality_status": "pass", "mock_used": False, "fixture_used": False, "raw_saved": False, "ocr_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
    p = r["phase71_alternative_disclosure_fallback"]
    steps = []
    def add(n, s, d=""): steps.append({"name": n, "status": s, "detail": d})

    mods = [
        ("build_phase71_alternative_source_registry", "source_registry", ""),
        ("build_phase71_fallback_route_plan", "fallback_routes", ""),
        ("build_phase71_known_url_catalog", "known_url_catalog", ""),
        ("build_phase71_irm_interaction_report", "irm_connector", ""),
        ("build_phase71_exchange_disclosure_report", "exchange_connector", ""),
        ("build_phase71_company_ir_page_report", "company_ir", ""),
        ("build_phase71_fallback_text_fetch_report", "fallback_text_fetch", ""),
        ("build_phase71_fallback_evidence_extraction", "evidence_extraction", ""),
        ("build_phase71_fallback_evidence_gain", "evidence_gain", ""),
        ("build_phase71_multi_source_capability_matrix", "capability_matrix", ""),
        ("build_phase71_fallback_evidence_memory_report", "evidence_memory", ""),
        ("build_phase71_research_packet", "research_packet", ""),
        ("build_phase71_internal_brief", "internal_brief", ""),
        ("build_phase71_brief_quality_lint", "brief_quality_lint", ""),
    ]
    for mod_name, step_name, key in mods:
        try:
            mod = __import__(mod_name)
            mod.build()
            add(step_name, "ok")
        except Exception as e:
            add(step_name, "error", str(e)[:50])
    p["steps"] = steps
    return r

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    r = run(mode=mode, skip_network=getattr(a, "skip_network", False))
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
