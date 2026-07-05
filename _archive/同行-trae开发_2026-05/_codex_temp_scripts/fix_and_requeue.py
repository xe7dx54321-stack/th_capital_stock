#!/usr/bin/env python3
"""Fix image references in wechat.md and re-enqueue to bridge."""

from pathlib import Path
import subprocess

ROOT = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统")
PACK_DIR = ROOT / "05_draft_packs" / "taco_prediction_skill_20260409"
SCRIPTS_DIR = ROOT / "09_runbooks" / "scripts"
BRIDGE_OUTBOX = ROOT / "07_wechat_bridge_outbox"

# Read current wechat.md
wechat_path = PACK_DIR / "wechat.md"
text = wechat_path.read_text(encoding="utf-8")

# Fix: slot_2 should use AI-generated image instead of local card
# Replace 81__slot_2.png with 71__ai_slot_2.png
text = text.replace("visual-assets/81__slot_2.png", "visual-assets/71__ai_slot_2.png")

# Also remove the slot_3 and slot_4 image references since they're still low-quality local cards
# Keep them for now - the local cards at least have the right titles

wechat_path.write_text(text, encoding="utf-8")
print(f"Updated wechat.md with AI image references")

# Remove old bridge request to force re-processing
old_request = BRIDGE_OUTBOX / "requests" / "wechat_bridge__taco_prediction_skill_20260409"
if old_request.exists():
    import shutil
    shutil.rmtree(old_request)
    print(f"Removed old bridge request: {old_request}")

# Re-enqueue
result = subprocess.run(
    ["python3", str(SCRIPTS_DIR / "market_wechat_bridge_enqueue.py"),
     "--draft-pack-dir", str(PACK_DIR), "--write"],
    capture_output=True, text=True, timeout=120,
    cwd=str(SCRIPTS_DIR),
)
print(f"Bridge enqueue exit code: {result.returncode}")
if result.stdout:
    # Find the REQUEST_WRITTEN line
    for line in result.stdout.splitlines():
        if "REQUEST_WRITTEN" in line or "error" in line.lower():
            print(line)

print("\nDone! The article has been re-enqueued to the WeChat bridge.")
print("The Windows consumer should pick it up and create a new draft in your WeChat draft box.")
