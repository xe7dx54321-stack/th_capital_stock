import json
from pathlib import Path

runs_dir = Path("/Users/apple/.openclaw/cron/runs")

for name in ["5f651e5c-6f6b-4da8-9b2b-0d7e4f7c1005.jsonl", "5f651e5c-6f6b-4da8-9b2b-0d7e4f7c1010.jsonl"]:
    fpath = runs_dir / name
    if not fpath.exists():
        print(f"NOT FOUND: {name}")
        continue
    print(f"\n=== {name} ===")
    lines = fpath.read_text().strip().splitlines()
    for line in lines[-5:]:
        obj = json.loads(line)
        ts = obj.get("timestamp", obj.get("started_at", ""))
        status = obj.get("status", obj.get("result", ""))
        note = str(obj.get("note", obj.get("summary", "")))[:200]
        print(f"  {ts} | {status} | {note}")
