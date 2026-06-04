import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    from smr_phase164_console_data import build_console_data_model
    model = build_console_data_model()
    cards = model["phase164_console_data_model"]["cards"]
    rows = [{"ticker": c["ticker"], "snapshot": c["snapshot_status"], "completeness": c["completeness_pct"], "monitoring": c["monitoring_signal"], "activation": c["activation_readiness"]} for c in cards]
    output = {"phase164_console_board": {"total": len(rows), "deferred": sum(1 for r in rows if r["snapshot"] == "deferred"), "live": sum(1 for r in rows if r["snapshot"] != "deferred"), "console_not_approval": True, "rows": rows, "mock_used": False, "fixture_used": False}}
    if mode == "markdown":
        print("# Phase164 Hydration Console Board")
        print(f"| Ticker | Snapshot | Completeness | Monitoring | Activation |")
        print(f"|--------|----------|-------------|------------|------------|")
        for r in rows: print(f"| {r['ticker']} | {r['snapshot']} | {r['completeness']:.0%} | {r['monitoring']} | {r['activation']} |")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
