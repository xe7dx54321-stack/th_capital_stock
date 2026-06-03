def build_backlog_update():
    items = [
        {"id": "BL-141-01", "title": "Add ticker detail deep-dive pages", "priority": "medium", "status": "backlog"},
        {"id": "BL-141-02", "title": "Add interactive thesis status timeline", "priority": "low", "status": "backlog"},
        {"id": "BL-141-03", "title": "Resolve 300394 CNINFO org_id", "priority": "high", "status": "blocked", "blocker": "cninfo_org_id_missing"},
        {"id": "BL-141-04", "title": "Source upgrade for 688041 valuation", "priority": "medium", "status": "tracking"},
    ]
    return {
        "phase141_backlog_update": {
            "items": len(items),
            "backlog": items,
            "not_trade": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
