def build_agent_loop_bridge(mode="skip-network"):
    tasks = []
    tickers = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
    for tk in tickers:
        tasks.append({
            "ticker": tk,
            "task_type": "hydrate_candidate_data",
            "status": "pending_research" if mode == "skip-network" else "ready",
            "llm_api_called": False,
            "live_llm_call_allowed": False
        })
    return {
        "phase164_agent_loop_bridge": {
            "total_tasks": len(tasks),
            "research_only": True,
            "llm_api_called": False,
            "live_llm_call_allowed": False,
            "tasks": tasks,
            "mock_used": False, "fixture_used": False
        }
    }

def build_scheduling_preview(mode="skip-network"):
    return {
        "phase164_scheduling_preview": {
            "scheduler_registered": False,
            "registration_status": "preview_only_not_real_registration",
            "mode": mode,
            "preview_not_execution": True,
            "mock_used": False, "fixture_used": False
        }
    }
