import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
def main(mode="json"):
    output = {"phase164_console_brief": {"title": "Candidate Hydration Console Brief", "summary": "Phase164 integrates 13-candidate hydration data into local HTML console with Agent Loop connectivity.", "key_findings": ["13 hydration cards rendered in console", "10 navigation sections (summary/cards/details/freshness/limitations/monitoring/feed/queue/daily/activation)", "Network mode semantics clarified for dry-run/execute/skip-network", "Valuation panel: 0 target prices", "News panel: 0 trade signals", "Agent loop bridge: research only, no LLM calls", "Activation precheck: 0 executions", "300394/688041 constraints preserved"], "mock_used": False, "fixture_used": False}}
    if mode == "markdown":
        print("# Hydration Console Brief")
        for f in output["phase164_console_brief"]["key_findings"]: print(f"- {f}")
    else: print(json.dumps(output, ensure_ascii=False, indent=2))
if __name__ == "__main__": main("markdown" if "--markdown" in sys.argv else "json")
