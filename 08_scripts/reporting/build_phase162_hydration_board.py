import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

def main(mode="json"):
    from smr_phase162_universe import build_hydration_universe
    from smr_phase162_classifier import classify_hydration_status
    from smr_phase162_scoring import score_evidence_readiness

    universe = build_hydration_universe()
    targets = universe["phase162_hydration_universe"]["targets"]
    classifier = classify_hydration_status(targets)
    readiness = score_evidence_readiness(targets)

    rows = []
    c_map = {r["ticker"]: r for r in classifier["phase162_hydration_classifier"]["results"]}
    r_map = {r["ticker"]: r for r in readiness["phase162_evidence_readiness_scorer"]["results"]}
    for t in targets:
        tk = t["ticker"]
        rows.append({
            "ticker": tk, "market": t["market"], "sector": t.get("sector",""),
            "hydration": c_map.get(tk, {}).get("hydration_status", "unknown"),
            "readiness": r_map.get(tk, {}).get("readiness_tier", "unknown")
        })

    output = {
        "phase162_hydration_board": {
            "targets_total": len(targets),
            "full_hydration": classifier["phase162_hydration_classifier"]["full_hydration_ready"],
            "partial_hydration": classifier["phase162_hydration_classifier"]["partial_hydration_ready"],
            "blocked": classifier["phase162_hydration_classifier"]["blocked"],
            "markets": {"US": 13},
            "rows": rows,
            "hydration_not_approval": True,
            "mock_used": False, "fixture_used": False
        }
    }
    if mode == "markdown":
        print("# Phase162 Hydration Board")
        print(f"| Ticker | Market | Hydration | Readiness |")
        print(f"|--------|--------|-----------|-----------|")
        for r in rows:
            print(f"| {r['ticker']} | {r['market']} | {r['hydration']} | {r['readiness']} |")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    mode = "json"; [setattr(__builtins__, 'mode', 'markdown') if '--markdown' in sys.argv else None]
    main("markdown" if "--markdown" in sys.argv else "json")
