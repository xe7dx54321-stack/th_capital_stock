# Phase175 config loader
import json, os

def load_phase175_config():
    p = "config/phase175_research_task_runner.json"
    if not os.path.exists(p):
        return {"phase175_config":{"status":"config_missing"}}
    with open(p,"r",encoding="utf-8-sig") as f:
        c = json.load(f)
    return {"phase175_config":{
        "status":"loaded","phase":"phase175",
        "strategy":c["strategy"],"research_only":True,
        "task_count_total":c["task_count_total"],
        "candidate_count":c["candidate_count"],
        "agent_types":c["agent_types"],
        "execution_mode":"local_research_artifact_generation",
        "real_llm_allowed":False,"broker_allowed":False,
        "artifacts_path_ignored":True,
        "mock_used":False,"fixture_used":False
    }}
