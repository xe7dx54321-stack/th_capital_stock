import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase93Config(unittest.TestCase):
    def test_load(self):
        from smr_phase93_config import load_config
        cfg=load_config();self.assertEqual(cfg["phase"],"phase93")
    def test_universe(self):
        from smr_phase93_config import get_universe
        self.assertEqual(len(get_universe()),8)
    def test_customer_signals(self):
        from smr_phase93_config import get_customer_signals
        self.assertEqual(len(get_customer_signals()),10)
    def test_supply_signals(self):
        from smr_phase93_config import get_supply_signals
        self.assertEqual(len(get_supply_signals()),9)
    def test_key_customers(self):
        from smr_phase93_config import get_key_customers
        self.assertGreater(len(get_key_customers("NVDA")),3)
    def test_no_mock(self):
        from smr_phase93_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestCustomerRegistry(unittest.TestCase):
    def test_build(self):
        from smr_phase93_customer_source_registry import build_customer_source_registry
        r=build_customer_source_registry()
        self.assertGreater(r["phase93_customer_source_registry"]["customer_sources_registered"],8)
    def test_no_mock(self):
        from smr_phase93_customer_source_registry import build_customer_source_registry
        self.assertFalse(build_customer_source_registry()["phase93_customer_source_registry"]["mock_used"])

class TestSupplyRegistry(unittest.TestCase):
    def test_build(self):
        from smr_phase93_supply_chain_source_registry import build_supply_chain_source_registry
        r=build_supply_chain_source_registry()
        self.assertGreater(r["phase93_supply_chain_source_registry"]["supply_chain_sources_registered"],8)
    def test_no_mock(self):
        from smr_phase93_supply_chain_source_registry import build_supply_chain_source_registry
        self.assertFalse(build_supply_chain_source_registry()["phase93_supply_chain_source_registry"]["mock_used"])

class TestEntityResolver(unittest.TestCase):
    def test_build(self):
        from smr_phase93_entity_resolver import build_entity_resolver
        r=build_entity_resolver()
        self.assertEqual(r["phase93_entity_resolver"]["tickers_resolved"],8)
    def test_nvda_has_customers(self):
        from smr_phase93_entity_resolver import build_entity_resolver
        r=build_entity_resolver()
        nvda=[e for e in r["phase93_entity_resolver"]["entities"] if e["ticker"]=="NVDA"][0]
        self.assertGreater(len(nvda["key_customers"]),0)

class TestCustomerExploration(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        r=explore_customer_sources("dry-run")
        self.assertEqual(r["phase93_customer_source_exploration"]["mode"],"dry-run")
    def test_execute(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        r=explore_customer_sources("execute")
        self.assertEqual(r["phase93_customer_source_exploration"]["mode"],"execute")
        self.assertGreater(r["phase93_customer_source_exploration"]["customer_capex_hits"],0)
    def test_8_tickers(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        r=explore_customer_sources("execute")
        self.assertEqual(r["phase93_customer_source_exploration"]["tickers_explored"],8)

class TestSupplyExploration(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase93_supply_exploration import explore_supply_sources
        r=explore_supply_sources("dry-run")
        self.assertEqual(r["phase93_supply_source_exploration"]["mode"],"dry-run")
    def test_execute(self):
        from smr_phase93_supply_exploration import explore_supply_sources
        r=explore_supply_sources("execute")
        self.assertGreater(r["phase93_supply_source_exploration"]["supply_chain_hits"],0)

class TestEvidence(unittest.TestCase):
    def test_extract(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_evidence_extraction import extract_evidence
        ce=explore_customer_sources("execute")
        se=explore_supply_sources("execute")
        r=extract_evidence(ce,se)
        self.assertGreater(r["phase93_evidence_extraction"]["customer_evidence_created"],0)
    def test_cannot_conclude(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_evidence_extraction import extract_evidence
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        r=extract_evidence(ce,se)
        for rec in r["phase93_evidence_extraction"]["evidence_records"]:
            for item in rec.get("customer_evidence",[]):
                self.assertIn("cannot_conclude",item)

class TestGateGuard(unittest.TestCase):
    def test_gate(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_evidence_extraction import extract_evidence
        from smr_phase93_quality_gate import run_quality_gate
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        ev=extract_evidence(ce,se);r=run_quality_gate(ev)
        gs=r["phase93_quality_gate"]["gate_summary"]
        self.assertGreaterEqual(gs["passed"]+gs["review_required"]+gs["rejected"],1)
    def test_guard_pass(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_evidence_extraction import extract_evidence
        from smr_phase93_quality_gate import run_quality_gate
        from smr_phase93_cannot_conclude_guard import run_cannot_conclude_guard
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        ev=extract_evidence(ce,se);gate=run_quality_gate(ev)
        r=run_cannot_conclude_guard(ev)
        self.assertEqual(r["phase93_cannot_conclude_guard"]["violations_found"],0)

class TestCoverage(unittest.TestCase):
    def test_matrix(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_coverage_matrices import build_coverage_matrices
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        r=build_coverage_matrices(ce,se)
        self.assertEqual(r["phase93_customer_coverage_matrix"]["tickers_total"],8)
    def test_300394_blocked(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_coverage_matrices import build_coverage_matrices
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        r=build_coverage_matrices(ce,se)
        row=[r2 for r2 in r["phase93_customer_coverage_matrix"]["coverage_rows"] if r2["ticker"]=="300394.SZ"][0]
        self.assertEqual(row["customer_capex_coverage_status"],"blocked")

class TestLinkage(unittest.TestCase):
    def test_build(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_linkage_builder import build_linkage
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        r=build_linkage(ce,se)
        self.assertGreater(r["phase93_linkage_builder"]["total_customer_links"]+r["phase93_linkage_builder"]["total_supply_links"],0)

class TestOrderDB(unittest.TestCase):
    def test_foundation(self):
        from smr_phase93_structured_order_db import build_order_db_foundation
        r=build_order_db_foundation("dry-run")
        self.assertGreater(len(r["phase93_structured_order_db_foundation"]["fields"]),5)
    def test_path_ignored(self):
        from smr_phase93_structured_order_db import build_order_db_foundation
        r=build_order_db_foundation("dry-run")
        self.assertTrue(r["phase93_structured_order_db_foundation"]["db_path_ignored"])

class TestGapCloseout(unittest.TestCase):
    def test_cl(self):
        from smr_phase93_customer_exploration import explore_customer_sources
        from smr_phase93_supply_exploration import explore_supply_sources
        from smr_phase93_coverage_matrices import build_coverage_matrices
        from smr_phase93_gap_closeout import build_gap_closeout
        ce=explore_customer_sources("execute");se=explore_supply_sources("execute")
        cm=build_coverage_matrices(ce,se);r=build_gap_closeout(cm)
        self.assertEqual(r["phase93_hard_data_gap_closeout"]["total_tickers"],8)

class TestBacklog(unittest.TestCase):
    def test_build(self):
        from smr_phase93_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase93_backlog_update"]["backlog_items"],10)
    def test_recommendation(self):
        from smr_phase93_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertIn("product_pricing",r["phase93_backlog_update"]["phase94_recommendation"])

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase93_customer_supply_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO();ctx=contextlib.redirect_stdout(buf)
            with ctx:rm()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["phase93_customer_supply_pipeline"]["mode"],"dry-run")
        finally:sys.argv=o
    def test_execute(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase93_customer_supply_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO();ctx=contextlib.redirect_stdout(buf)
            with ctx:rm()
            d=json.loads(buf.getvalue())
            p=d["phase93_customer_supply_pipeline"]
            self.assertEqual(p["mode"],"execute");self.assertEqual(p["tickers_explored"],8)
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase93_customer_supply_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO();ctx=contextlib.redirect_stdout(buf)
            with ctx:rm()
            d=json.loads(buf.getvalue())
            p=d["phase93_customer_supply_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestDashboard(unittest.TestCase):
    def test_json(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase93_hard_source_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO();ctx=contextlib.redirect_stdout(buf)
            with ctx:dm()
            d=json.loads(buf.getvalue())
            self.assertIn("customer_hits",d["summary"])
        finally:sys.argv=o
    def test_no_mock(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase93_hard_source_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO();ctx=contextlib.redirect_stdout(buf)
            with ctx:dm()
            d=json.loads(buf.getvalue())
            self.assertFalse(d["summary"]["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
