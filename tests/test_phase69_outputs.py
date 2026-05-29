import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestCapabilityMatrix(unittest.TestCase):
    def test_matrix_output(self):
        from build_phase69_multi_ticker_capability_matrix import build
        r = build()
        cm = r['multi_ticker_capability_matrix']
        self.assertEqual(cm['tickers_checked'], 3)
        self.assertGreaterEqual(cm['full_chain_available'], 1)
        self.assertGreaterEqual(cm['blocked'], 1)

    def test_pending_zero(self):
        from build_phase69_multi_ticker_capability_matrix import build
        r = build()
        cm = r['multi_ticker_capability_matrix']
        self.assertEqual(cm['pending_created'], 0)
        self.assertEqual(cm['paper_order_created'], 0)
        self.assertEqual(cm['real_trade_created'], 0)

class TestResearchPacket(unittest.TestCase):
    def test_no_trade_advice(self):
        from build_phase69_multi_ticker_research_packet import build
        r = build()
        pkt = r['multi_ticker_research_packet']
        self.assertEqual(pkt['pending_created'], 0)
        self.assertEqual(pkt['paper_order_created'], 0)
        self.assertEqual(pkt['real_trade_created'], 0)

    def test_blocked_ticker_explained(self):
        from build_phase69_multi_ticker_research_packet import build
        r = build()
        pkt = r['multi_ticker_research_packet']
        blocked = [t for t in pkt['tickers'] if t['research_status'] == 'blocked_before_research']
        for b in blocked:
            self.assertIn('blocker', b)

class TestBrief(unittest.TestCase):
    def test_no_system_terms(self):
        from build_phase69_multi_ticker_internal_brief import build
        r = build()
        md = r['phase69_multi_ticker_internal_brief']['markdown']
        for term in ['candidate', 'pending', 'dashboard', 'validator', 'runner']:
            self.assertNotIn(term, md.lower())

    def test_no_trade_advice(self):
        from build_phase69_multi_ticker_internal_brief import build
        r = build()
        md = r['phase69_multi_ticker_internal_brief']['markdown']
        for term in ['买入', '卖出', '目标价', '仓位', '加仓']:
            self.assertNotIn(term, md)

    def test_has_structure(self):
        from build_phase69_multi_ticker_internal_brief import build
        r = build()
        md = r['phase69_multi_ticker_internal_brief']['markdown']
        self.assertIn('老板摘要', md)
        self.assertIn('研究员详情', md)

class TestLint(unittest.TestCase):
    def test_lint_pass(self):
        from build_phase69_multi_ticker_brief_quality_lint import build
        r = build()
        lt = r['multi_ticker_brief_quality_lint']
        self.assertEqual(lt['overall_status'], 'pass')
        self.assertEqual(lt['system_terms_found'], 0)
        self.assertEqual(lt['trade_advice_terms_found'], 0)

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        import sys; sys.path.insert(0, '08_scripts/jobs')
        from run_phase69_multi_ticker_disclosure_generalization import run
        r = run(mode='dry_run')
        p = r['phase69_multi_ticker_disclosure_generalization']
        self.assertGreater(len(p['steps']), 0)
        self.assertEqual(p['pending_created'], 0)

    def test_execute(self):
        import sys; sys.path.insert(0, '08_scripts/jobs')
        from run_phase69_multi_ticker_disclosure_generalization import run
        r = run(mode='execute')
        p = r['phase69_multi_ticker_disclosure_generalization']
        self.assertGreaterEqual(p['full_chain_available'], 1)

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        from build_phase69_multi_ticker_disclosure_dashboard import build
        r = build()
        s = r['summary']
        self.assertEqual(s['tickers_checked'], 3)
        self.assertEqual(s['pending_created'], 0)
        self.assertEqual(s['mock_used'], False)
        self.assertEqual(s['brief_quality_status'], 'pass')

if __name__ == '__main__': unittest.main()
