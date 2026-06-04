def build_backlog_update(evidence_filled=False):
    return {
        "phase166_backlog_update": {
            "backlog_entries_added": 13,
            "backlog_type": "live_evidence_fill_and_agent_rerun",
            "evidence_filled": evidence_filled,
            "agent_rerun_complete": True,
            "next_phase_ready": True,
            "research_only": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
