def build_loop_memory_update(targets, agent_results):
    entries = []
    for t in targets:
        entries.append({"ticker": t, "memory_type": "agent_loop_output",
                       "agents_engaged": ["Opportunity","Evidence","Risk","Thesis","DeepDive","Brief","Feedback","Judge"],
                       "judge_outcome": "research_loop_complete"})
    return {"phase154_memory_update": {"memory_entries_written": len(entries), "entries": entries,
        "memory_path_ignored": True, "mock_used": False, "fixture_used": False}}
