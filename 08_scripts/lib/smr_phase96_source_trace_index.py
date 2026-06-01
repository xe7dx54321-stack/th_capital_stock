import json,os
def build_source_trace_index(records):
    """Build a source trace index for all hard data records."""
    traces={}
    for r in records:
        st=r.get("source_trace","unknown")
        traces[st]=traces.get(st,0)+1
    rows=[{"source_trace":k,"record_count":v} for k,v in sorted(traces.items())]
    return {"phase96_source_trace_index":{"unique_traces":len(traces),"total_traced_records":sum(traces.values()),"rows":rows,"mock_used":False,"fixture_used":False}}
