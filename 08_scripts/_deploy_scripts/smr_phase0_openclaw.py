#!/usr/bin/env python3
"""Phase 0-4: Modify openclaw.json to add 7 SMR agents."""

import json
import shutil
import os

CONFIG_PATH = "/Users/apple/.openclaw/openclaw.json"
BACKUP_PATH = "/Users/apple/.codex/tmp/openclaw.json.bak.pre-smr"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

shutil.copy2(CONFIG_PATH, BACKUP_PATH)
print(f"Backup saved to {BACKUP_PATH}")

existing_ids = {a["id"] for a in config["agents"]["list"]}
print(f"Existing agents: {sorted(existing_ids)}")

smr_agents = [
    {
        "id": "smr-lead",
        "workspace": "/Users/apple/.openclaw/workspace-smr-lead",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"},
        "groupChat": {
            "mentionPatterns": ["@smr-lead", "@二级市场"]
        }
    },
    {
        "id": "smr-researcher",
        "workspace": "/Users/apple/.openclaw/workspace-smr-researcher",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"}
    },
    {
        "id": "smr-analyst",
        "workspace": "/Users/apple/.openclaw/workspace-smr-analyst",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"}
    },
    {
        "id": "smr-advisor",
        "workspace": "/Users/apple/.openclaw/workspace-smr-advisor",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"}
    },
    {
        "id": "smr-portfolio-mgr",
        "workspace": "/Users/apple/.openclaw/workspace-smr-portfolio-mgr",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"}
    },
    {
        "id": "smr-risk-controller",
        "workspace": "/Users/apple/.openclaw/workspace-smr-risk-controller",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "1h"}
    },
    {
        "id": "smr-brief-writer",
        "workspace": "/Users/apple/.openclaw/workspace-smr-brief-writer",
        "model": "minimax-cn/MiniMax-M2.7",
        "heartbeat": {"every": "3h"}
    },
]

for agent in smr_agents:
    if agent["id"] not in existing_ids:
        config["agents"]["list"].append(agent)
        print(f"  Added agent: {agent['id']}")
    else:
        print(f"  Skipped (already exists): {agent['id']}")

smr_allow_ids = [
    "smr-lead", "smr-researcher", "smr-analyst",
    "smr-advisor", "smr-portfolio-mgr", "smr-risk-controller",
    "smr-brief-writer"
]

current_allow = config["tools"]["agentToAgent"]["allow"]
for aid in smr_allow_ids:
    if aid not in current_allow:
        current_allow.append(aid)
        print(f"  Added to agentToAgent.allow: {aid}")
    else:
        print(f"  Skipped (already in allow): {aid}")

with open(CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

total_agents = len(config["agents"]["list"])
total_allow = len(config["tools"]["agentToAgent"]["allow"])
print(f"\nDone! Total agents: {total_agents}, agentToAgent.allow: {total_allow}")
print(f"Config written to {CONFIG_PATH}")
