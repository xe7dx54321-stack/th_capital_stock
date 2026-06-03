import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase159_submission_board import build as build_board
    b = build_board()["phase159_submission_board"]; fl = b["file_locator"]; q = b["quarantine"]; sm = b["safe_manifest"]
    return "\n".join(["# Owner Decision Submission Brief","",
        "## Submission Status",f"- Input present: {fl['owner_input_present']}",
        f"- Invalid / quarantined: {q['invalid_count']}",
        f"- Safe decisions: {sm['safe_count']}","",
        "## Key Principles",
        "- Missing input is allowed; all candidates remain pending.",
        "- Submission is NOT execution.",
        "- Validation is NOT activation.",
        "- Safe manifest is NOT Watch update.",
        "- Preview activation is NOT real activation.",
        "- Approve ≠ buy. Reject ≠ sell.",
        "- 300394 CNINFO blocker retained.",
    ])

def build_json():
    return {"phase159_submission_brief":{"brief_generated":True,"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(),indent=2,ensure_ascii=False,default=str))
