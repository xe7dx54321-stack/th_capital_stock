import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestConfig(unittest.TestCase):
    def test_load(self):
        from smr_phase94_config import load_config
        self.assertEqual(load_config()["phase"],"phase94")
    def test_universe(self):
        from smr_phase94_config import get_universe
        self.assertEqual(len(get_universe()),8)
    def test_signals(self):
        from smr_phase94_config import get_pricing_signals, get_guidance_signals
        self.assertEqual(len(get_pricing_signals()),14);self.assertEqual(len(get_guidance_signals()),14)
    def test_products(self):
        from smr_phase94_config import get_key_products
        self.assertGreater(len(get_key_products("NVDA")),5)
    def test_no_mock(self):
        from smr_phase94_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestRegistries(unittest.TestCase):
    def test_pricing(self):
        from smr_phase94_pricing_registry import build_pricing_registry
        r=build_pricing_registry()
        self.assertGreater(r["phase94_pricing_registry"]["pricing_sources"],8)
    def test_guidance(self):
        from smr_phase94_guidance_registry import build_guidance_registry
        r=build_guidance_registry()
        self.assertGreater(r["phase94_guidance_registry"]["guidance_sources"],10)
    def test_no_mock(self):
        from smr_phase94_pricing_registry import build_pricing_registry
        self.assertFalse(build_pricing_registry()["phase94_pricing_registry"]["mock_used"])

class TestEntityResolver(unittest.TestCase):
    def test_build(self):
        from smr_phase94_entity_resolver import build_entity_resolver
        r=build_entity_resolver()
        self.assertEqual(r["phase94_entity_resolver"]["tickers_resolved"],8)
    def test_nvda_products(self):
        from smr_phase94_entity_resolver import build_entity_resolver
        r=build_entity_resolver()
        n=[e for e in r["phase94_entity_resolver"]["entities"] if e["ticker"]=="NVDA"][0]
        self.assertIn("H100",n["key_products"])

class TestExplorations(unittest.TestCase):
    def test_pricing_dry(self):
        from smr_phase94_pricing_exploration import explore_pricing
        r=explore_pricing("dry-run")
        self.assertEqual(r["phase94_pricing_exploration"]["mode"],"dry-run")
    def test_pricing_exec(self):
        from smr_phase94_pricing_exploration import explore_pricing
        r=explore_pricing("execute")
        self.assertGreater(r["phase94_pricing_exploration"]["hits"],0)
    def test_guidance_exec(self):
        from smr_phase94_guidance_exploration import explore_guidance
        r=explore_guidance("execute")
        self.assertGreater(r["phase94_guidance_exploration"]["hits"],0)
    def test_8_tickers(self):
        from smr_phase94_pricing_exploration import explore_pricing
        self.assertEqual(explore_pricing("execute")["phase94_pricing_exploration"]["tickers"],8)

class TestEvidence(unittest.TestCase):
    def test_extract(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_evidence import extract_evidence
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        r=extract_evidence(pe,ge)
        self.assertGreater(r["phase94_evidence"]["pricing_evidence"],0)
    def test_cannot_conclude(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_evidence import extract_evidence
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        r=extract_evidence(pe,ge)
        for rec in r["phase94_evidence"]["records"]:
            for it in rec.get("pricing_ev",[]):
                self.assertIn("cannot",it)

class TestGateGuard(unittest.TestCase):
    def test_gate(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_evidence import extract_evidence
        from smr_phase94_quality_gate import run_gate
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        ev=extract_evidence(pe,ge);r=run_gate(ev)
        gs=r["phase94_gate"]["summary"]
        self.assertGreaterEqual(gs["passed"]+gs["review"]+gs["rejected"],1)
    def test_guard_pass(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_evidence import extract_evidence
        from smr_phase94_guard import run_guard
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        ev=extract_evidence(pe,ge);r=run_guard(ev)
        self.assertEqual(r["phase94_guard"]["violations"],0)

class TestCoverage(unittest.TestCase):
    def test_matrix(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_coverage import build_coverage
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        r=build_coverage(pe,ge)
        self.assertEqual(r["phase94_pricing_coverage"]["total"],8)
    def test_300394(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_coverage import build_coverage
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        r=build_coverage(pe,ge)
        row=[r2 for r2 in r["phase94_pricing_coverage"]["rows"] if r2["ticker"]=="300394.SZ"][0]
        self.assertEqual(row["status"],"blocked")

class TestLinkage(unittest.TestCase):
    def test_build(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_linkage import build_linkage
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        r=build_linkage(pe,ge)
        self.assertGreater(r["phase94_linkage"]["pricing_links"],0)

class TestGapBacklog(unittest.TestCase):
    def test_closeout(self):
        from smr_phase94_pricing_exploration import explore_pricing
        from smr_phase94_guidance_exploration import explore_guidance
        from smr_phase94_coverage import build_coverage
        from smr_phase94_gap_backlog import build_gap_closeout
        pe=explore_pricing("execute");ge=explore_guidance("execute")
        cm=build_coverage(pe,ge);r=build_gap_closeout(cm)
        self.assertEqual(r["phase94_gap_closeout"]["total"],8)
    def test_backlog(self):
        from smr_phase94_gap_backlog import build_backlog
        r=build_backlog()
        self.assertEqual(r["phase94_backlog"]["items"],10)
    def test_recommendation(self):
        from smr_phase94_gap_backlog import build_backlog
        r=build_backlog()
        self.assertIn("300394",r["phase94_backlog"]["phase95_recommendation"])

class TestRunner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase94_pricing_guidance_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["phase94_pipeline"]["mode"],"dry-run")
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase94_pricing_guidance_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())
            p=d["phase94_pipeline"]
            self.assertEqual(p["mode"],"execute");self.assertEqual(p["tickers"],8)
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase94_pricing_guidance_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())
            p=d["phase94_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestDashboard(unittest.TestCase):
    def test_json(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase94_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())
            self.assertIn("pricing_hits",d["summary"])
        finally:sys.argv=o
    def test_no_mock(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase94_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())
            self.assertFalse(d["summary"]["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
