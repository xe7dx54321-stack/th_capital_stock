import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase142_detail_quality_gate import run_detail_quality_gate

class TestQualityGate(unittest.TestCase):
    def test_8_pages_pass(self):
        pages = {f'TICKER{i}': '<!DOCTYPE html><title>Test</title>Research Console Research-only timeline evidence-chain evidence' for i in range(8)}
        r = run_detail_quality_gate(pages)
        self.assertEqual(r['phase142_detail_quality_gate']['overall_status'], 'pass')
    def test_7_pages_fail(self):
        pages = {f'TICKER{i}': '<!DOCTYPE html><title>Test</title>Research Console Research-only timeline evidence-chain evidence' for i in range(7)}
        r = run_detail_quality_gate(pages)
        self.assertEqual(r['phase142_detail_quality_gate']['overall_status'], 'fail')

if __name__ == '__main__':
    unittest.main()
