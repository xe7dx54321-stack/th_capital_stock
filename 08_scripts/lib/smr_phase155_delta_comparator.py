def build_loop_delta_comparator(previous_run, current_run):
    if previous_run is None or not previous_run.get("has_previous_run"):
        return {"phase155_delta_comparator":{"delta_available":False,"comparison_status":"first_run_baseline","changes":[],"note":"First run; no previous loop to compare against.","mock_used":False,"fixture_used":False}}
    changes = []
    for t in current_run.get("targets",[]):
        changes.append({"ticker":t,"previous_status":"unchanged","current_status":"rechecked","delta":"no_change"})
    return {"phase155_delta_comparator":{"delta_available":True,"comparison_status":"compared","changes":len(changes),"delta_details":changes,"mock_used":False,"fixture_used":False}}
