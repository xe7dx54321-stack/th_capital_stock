#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts")

from market_morning_flash_publish_guard import *
from pathlib import Path

queue_root = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统/06_publish_queue")

for path in sorted(queue_root.glob("*__publish-queue-item.md")):
    fields = parse_fields(path)
    if clean(fields.get("delivery_lane", "")) != "morning_flash":
        continue
    if clean(fields.get("status", "")) != "deferred":
        continue
    pack_dir = draft_pack_dir(fields)
    preflight_path = pack_dir / "morning-flash-preflight.md"
    reviewer_path = pack_dir / "morning-flash-reviewer-checklist.md"
    leader_path = pack_dir / "morning-flash-leader-checklist.md"

    pf_status = "N/A"
    if preflight_path.exists():
        pf = parse_fields(preflight_path)
        pf_status = clean(pf.get("technical_preflight_status", "N/A"))

    reviewer_status = "pass" if checklist_passed(reviewer_path) else "not_pass"
    leader_status = "pass" if checklist_passed(leader_path) else "not_pass"
    blockers = structural_preflight_blockers(path)

    print(f"Queue: {path.name}")
    print(f"  preflight: {pf_status}")
    print(f"  reviewer: {reviewer_status}")
    print(f"  leader: {leader_status}")
    print(f"  structural_blockers: {blockers}")
    recoverable = pf_status == "pass" and reviewer_status == "pass" and leader_status == "pass" and not blockers
    print(f"  recoverable: {recoverable}")
    print()
