import json
from pathlib import Path

SANDBOX_INPUT = "09_runbooks/generated/phase160_sandbox_input.json"
SANDBOX_OUTPUT = "09_runbooks/generated/phase160_sandbox_validation_results.json"

def write_sandbox_input(example):
    p = Path(__file__).resolve().parent.parent.parent / SANDBOX_INPUT
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(example.get("input_json", {}), fh, ensure_ascii=False, indent=2)
    return {
        "phase160_sandbox_input_writer": {
            "written": True,
            "path": SANDBOX_INPUT,
            "path_ignored": True,
            "example_id": example.get("example_id", ""),
            "real_owner_input_overwritten": False,
            "mock_used": False,
            "fixture_used": False
        }
    }

def run_sandbox_validation(example):
    candidates = [
        {"ticker": "MRVL", "name": "Marvell", "market": "US"},
        {"ticker": "AMAT", "name": "Applied Materials", "market": "US"},
        {"ticker": "LRCX", "name": "Lam Research", "market": "US"},
        {"ticker": "KLAC", "name": "KLA", "market": "US"},
        {"ticker": "INTC", "name": "Intel", "market": "US"},
        {"ticker": "SNPS", "name": "Synopsys", "market": "US"},
        {"ticker": "CDNS", "name": "Cadence", "market": "US"},
        {"ticker": "CRM", "name": "Salesforce", "market": "US"}
    ]
    allowed_decisions = [
        "approve_research_activation", "defer_to_next_review",
        "reject_for_now", "request_more_evidence", "confirm_identity_source"
    ]
    forbidden_terms = [
        "buy", "sell", "target_price", "position_sizing",
        "trade", "order", "short", "add", "reduce"
    ]
    valid_tiers = ["Core", "Watch", "Candidate"]
    candidate_tickers = {c["ticker"] for c in candidates}

    decisions = example.get("input_json", {}).get("decisions", [])
    results = []

    for d in decisions:
        ticker = d.get("ticker", "")
        decision = d.get("decision", "")
        rationale = d.get("rationale", "")
        tier = d.get("requested_tier", "")

        issues = []

        if ticker not in candidate_tickers:
            issues.append("unknown_candidate")
        if decision not in allowed_decisions:
            issues.append("invalid_decision")
        rationale_lower = rationale.lower()
        for ft in forbidden_terms:
            if ft.lower().replace("_", " ") in rationale_lower:
                issues.append(f"forbidden_term:{ft}")
        if not rationale.strip():
            issues.append("missing_rationale")
        if tier and tier not in valid_tiers:
            issues.append("invalid_tier")

        seen = set()
        for other in decisions:
            ot = other.get("ticker", "")
            if ot == ticker and id(other) != id(d) and ticker not in seen:
                issues.append("duplicate_ticker")
            seen.add(ticker)

        is_valid = len(issues) == 0
        results.append({
            "ticker": ticker,
            "decision": decision,
            "is_valid": is_valid,
            "issues": issues,
            "quarantine": not is_valid
        })

    safe = [r for r in results if r["is_valid"]]
    invalid = [r for r in results if not r["is_valid"]]
    quarantined = [r for r in results if r["quarantine"]]

    return {
        "phase160_sandbox_validation": {
            "example_id": example.get("example_id", ""),
            "example_name": example.get("example_name", ""),
            "total_decisions": len(results),
            "safe_count": len(safe),
            "invalid_count": len(invalid),
            "quarantine_count": len(quarantined),
            "preview_count": len(safe),
            "execution_count": 0,
            "results": results,
            "sandbox_not_execution": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def aggregate_sandbox_results(validation_results_list):
    all_safe = 0
    all_invalid = 0
    all_quarantine = 0
    all_preview = 0
    per_example = []

    for vr in validation_results_list:
        v = vr.get("phase160_sandbox_validation", {})
        all_safe += v.get("safe_count", 0)
        all_invalid += v.get("invalid_count", 0)
        all_quarantine += v.get("quarantine_count", 0)
        all_preview += v.get("preview_count", 0)
        per_example.append({
            "example_id": v.get("example_id", ""),
            "example_name": v.get("example_name", ""),
            "safe": v.get("safe_count", 0),
            "invalid": v.get("invalid_count", 0),
            "quarantine": v.get("quarantine_count", 0),
            "preview": v.get("preview_count", 0),
            "execution": 0
        })

    return {
        "phase160_sandbox_aggregator": {
            "total_examples": len(validation_results_list),
            "total_safe": all_safe,
            "total_invalid": all_invalid,
            "total_quarantine": all_quarantine,
            "total_preview": all_preview,
            "total_execution": 0,
            "per_example": per_example,
            "sandbox_not_execution": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
