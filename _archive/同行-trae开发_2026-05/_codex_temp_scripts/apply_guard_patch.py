#!/usr/bin/env python3
import re
from pathlib import Path

GUARD_SCRIPT = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts/market_morning_flash_publish_guard.py")

text = GUARD_SCRIPT.read_text(encoding="utf-8")
original = text

# Patch 1: Increase default limit from 1 to 2
text = text.replace(
    'parser.add_argument("--limit", type=int, default=1, help="Maximum items to auto-publish in one run")',
    'parser.add_argument("--limit", type=int, default=2, help="Maximum items to auto-publish in one run")'
)

# Patch 2: Add auto-recovery for deferred items in main()
old_block = '    if args.write:\n        for candidate in candidates:\n            refresh_preflight(candidate)\n            recover_morning_flash_gate(candidate, write=True)\n\n    decisions = [guard_decision(path) for path in candidates]'

new_block = '    if args.write:\n        for candidate in candidates:\n            refresh_preflight(candidate)\n            recover_morning_flash_gate(candidate, write=True)\n        candidates = _recover_deferred_items(candidates, args.date, queue_root)\n\n    decisions = [guard_decision(path) for path in candidates]'

text = text.replace(old_block, new_block)

# Patch 3: Add the _recover_deferred_items function before main()
recovery_func = '''
def _recover_deferred_items(
    candidates: list[Path], date_text: str, queue_root: Path
) -> list[Path]:
    """Re-include deferred morning_flash items whose three gates now pass."""
    token = date.fromisoformat(date_text).strftime("%Y%m%d")
    recovered: list[Path] = []
    for path in sorted(queue_root.glob("*__publish-queue-item.md")):
        fields = parse_fields(path)
        if clean(fields.get("delivery_lane", "")) != "morning_flash":
            continue
        if clean(fields.get("status", "")) != "deferred":
            continue
        if path in candidates:
            continue
        pack_dir = draft_pack_dir(fields)
        preflight_path = pack_dir / "morning-flash-preflight.md"
        reviewer_path = pack_dir / "morning-flash-reviewer-checklist.md"
        leader_path = pack_dir / "morning-flash-leader-checklist.md"
        if not preflight_path.exists():
            continue
        pf = parse_fields(preflight_path)
        if clean(pf.get("technical_preflight_status", "")) != "pass":
            continue
        if not checklist_passed(reviewer_path):
            continue
        if not checklist_passed(leader_path):
            continue
        blockers = structural_preflight_blockers(path)
        if blockers:
            continue
        updated = path.read_text(encoding="utf-8")
        updated = update_field(updated, "status", "waiting_human_publish")
        updated = update_field(updated, "manual_gate", "auto_recovered_from_deferred")
        note = merge_note(
            fields.get("notes", "n/a"),
            f"auto_recovered_at={now_cn().isoformat()} reason=three_gates_passed_after_deferred",
        )
        updated = update_field(updated, "notes", note)
        path.write_text(updated, encoding="utf-8")
        card_path = pack_dir / "00_draft-pack-card.md"
        if card_path.exists():
            card_text = card_path.read_text(encoding="utf-8")
            card_text = update_field(card_text, "status", "ready")
            card_text = update_field(card_text, "publish_gate", "auto_recovered")
            card_path.write_text(card_text, encoding="utf-8")
        recovered.append(path)
    if recovered:
        print(f"[recovery] {len(recovered)} deferred item(s) auto-recovered: {[p.name for p in recovered]}")
    return candidates + recovered


'''

text = text.replace(
    "\ndef main() -> None:",
    recovery_func + "def main() -> None:"
)

if text != original:
    GUARD_SCRIPT.write_text(text, encoding="utf-8")
    print(f"Patched {GUARD_SCRIPT}")
    print("Changes applied:")
    print("  1. limit default: 1 -> 2")
    print("  2. Added _recover_deferred_items() function")
    print("  3. Added auto-recovery call in main() after gate recovery")
else:
    print("No changes needed (pattern not found)")
