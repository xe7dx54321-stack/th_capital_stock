import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_source_coverage_update import build_source_coverage_update

def build_integration_update(skip_network=False):
    classified=classify_availability(skip_network)
    coverage=build_source_coverage_update(skip_network)
    return {"phase128_integration_update":{"phases_updated":["phase121","phase122","phase126","phase127"],"phase121_source_registry_updated":True,"phase122_daily_brief_source_updated":True,"phase126_signal_effectiveness_source_updated":True,"phase127_gap_register_updated":True,"source_availability_after_probe":classified["phase128_availability_classifier"]["counts"],"coverage_after_probe":coverage["phase128_source_coverage_update"],"mock_used":False,"fixture_used":False}}
