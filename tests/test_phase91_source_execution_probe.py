import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_source_inventory import build_source_inventory
from smr_phase91_source_execution_probe import run_probes

class TestProbe(unittest.TestCase):
    def test_dry_run(self):
        inv=build_source_inventory()
        result=run_probes(inv,"dry-run")
        self.assertEqual(result["phase91_source_execution_probe"]["probe_mode"],"dry-run")
    def test_skip_network(self):
        inv=build_source_inventory()
        result=run_probes(inv,"skip-network")
        self.assertEqual(result["phase91_source_execution_probe"]["probe_mode"],"skip-network")
    def test_execute_mode(self):
        inv=build_source_inventory()
        result=run_probes(inv,"execute")
        self.assertEqual(result["phase91_source_execution_probe"]["probe_mode"],"execute")
    def test_all_sources_probed(self):
        inv=build_source_inventory()
        result=run_probes(inv,"dry-run")
        self.assertEqual(result["phase91_source_execution_probe"]["sources_probed"],
                         inv["phase91_existing_source_inventory"]["sources_inventoried"])
