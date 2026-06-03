def build_loop_task_schema():
    return {"phase154_loop_task_schema": {
        "task_types": ["opportunity_scan","evidence_gather","risk_screen","thesis_propose",
                      "deep_dive_plan","brief_draft","feedback_collect","judge_review"],
        "task_structure": {"task_id": "string", "assigned_agent": "string", "target_ticker": "string",
                          "input_context": "dict", "output_deliverable": "dict",
                          "handoff_to": "string", "judge_review_result": "string"},
        "mock_used": False, "fixture_used": False,
    }}
