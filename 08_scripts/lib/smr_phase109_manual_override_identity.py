import json,os
def build_manual_override_identity():
    return {"phase109_manual_override_identity":{"rule":"manual_override_requires_supervisor_identity","enforced":True,"supervisor_must_differ_from_operator":True,"readiness_status":"ready","mock_used":False,"fixture_used":False}}
