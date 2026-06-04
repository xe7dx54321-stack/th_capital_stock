def build_activation_precheck(mode="skip-network"):
    tickers = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
    results = []
    for tk in tickers:
        results.append({
            "ticker": tk,
            "ready_for_activation": False,
            "reason": "network_data_required" if mode == "skip-network" else "owner_decision_required",
            "precheck_not_execution": True,
            "activation_execution_created": False
        })
    return {
        "phase164_activation_precheck": {
            "total": len(results),
            "ready": 0,
            "not_ready": len(results),
            "precheck_not_execution": True,
            "activation_execution_created": False,
            "results": results,
            "mock_used": False, "fixture_used": False
        }
    }
