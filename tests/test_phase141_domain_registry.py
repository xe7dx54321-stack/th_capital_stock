import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_domain_registry import build_domain_registry

class TestDomainRegistry(unittest.TestCase):
    def test_registry_builds(self):
        result = build_domain_registry()
        self.assertIn('phase141_domain_registry', result)
        reg = result['phase141_domain_registry']
        self.assertTrue(reg['all_research_only'])
        self.assertGreater(reg['total'], 10)
        self.assertIn('dashboard_data_model', reg['domains'])
        self.assertIn('html_quality_gate', reg['domains'])
        self.assertIn('cannot_conclude_guard', reg['domains'])

    def test_no_mock_fixture(self):
        result = build_domain_registry()
        reg = result['phase141_domain_registry']
        for k, v in reg['domains'].items():
            self.assertTrue(v.get('research_only', False))

if __name__ == '__main__':
    unittest.main()
