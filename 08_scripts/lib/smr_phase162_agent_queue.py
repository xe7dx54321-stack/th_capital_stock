def update_agent_task_queue(targets, mode="skip-network"):
    tasks = []
    for t in targets:
        ticker = t.get("ticker", "")
        tasks.append({
            "ticker": ticker,
            "task": "hydrate_financial_data",
            "status": "pending_network" if mode == "skip-network" else "ready",
            "priority": "medium",
            "no_trade_order": True,
            "no_target_price": True
        })
    return {
        "phase162_agent_task_queue": {
            "tasks_created": len(tasks),
            "pending_network": sum(1 for t in tasks if t["status"] == "pending_network"),
            "ready": sum(1 for t in tasks if t["status"] == "ready"),
            "no_trade_orders": True,
            "no_target_prices": True,
            "tasks": tasks,
            "mock_used": False,
            "fixture_used": False
        }
    }
