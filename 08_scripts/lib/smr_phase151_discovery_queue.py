def build_discovery_queue():
    discovered = [
        {"ticker": "MRVL", "name": "Marvell Technology", "market": "US", "discovery_source": "theme_based", "trigger": "AI networking/ASIC theme adjacent to NVDA/AVGO", "priority": "high", "status": "new"},
        {"ticker": "AMAT", "name": "Applied Materials", "market": "US", "discovery_source": "industry_chain", "trigger": "Semiconductor equipment; critical supplier to TSM", "priority": "high", "status": "new"},
        {"ticker": "LRCX", "name": "Lam Research", "market": "US", "discovery_source": "peer_based", "trigger": "Semiconductor equipment peer to AMAT, etch/deposition leader", "priority": "high", "status": "new"},
        {"ticker": "KLAC", "name": "KLA Corporation", "market": "US", "discovery_source": "industry_chain", "trigger": "Process control/metrology; critical for advanced node manufacturing", "priority": "medium", "status": "new"},
        {"ticker": "INTC", "name": "Intel", "market": "US", "discovery_source": "peer_based", "trigger": "Peer/competitor to NVDA/AMD; foundry strategy pivot", "priority": "medium", "status": "new"},
        {"ticker": "SNPS", "name": "Synopsys", "market": "US", "discovery_source": "industry_chain", "trigger": "EDA tools; critical for chip design; ANSYS acquisition", "priority": "medium", "status": "new"},
        {"ticker": "CDNS", "name": "Cadence Design Systems", "market": "US", "discovery_source": "industry_chain", "trigger": "EDA tools peer to SNPS; AI-driven design tools", "priority": "medium", "status": "new"},
        {"ticker": "CRM", "name": "Salesforce", "market": "US", "discovery_source": "customer_capex", "trigger": "Enterprise AI spend beneficiary; Agentforce platform", "priority": "low", "status": "new"},
    ]
    summary = {"total": len(discovered), "by_priority": {"high": sum(1 for d in discovered if d["priority"]=="high"), "medium": sum(1 for d in discovered if d["priority"]=="medium"), "low": sum(1 for d in discovered if d["priority"]=="low")}, "by_source": {s: sum(1 for d in discovered if d["discovery_source"]==s) for s in set(d["discovery_source"] for d in discovered)}}
    return {"phase151_discovery_queue": {"candidates_discovered": len(discovered), "queue": discovered, "summary": summary, "auto_add_to_watchlist": False, "mock_used": False, "fixture_used": False}}
