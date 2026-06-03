import unittest, sys, os, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase143_link_integrity_checker import check_link_integrity

class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, 'phase142_ticker_details'), exist_ok=True)
        for t in ['NVDA','AVGO','688041-SH','300308-SZ','002230-SZ','09988-HK','00700-HK','300394-SZ']:
            with open(os.path.join(self.tmp, 'phase142_ticker_details', f'{t}.html'), 'w') as f:
                f.write('Research Console detail-page thesis-timeline evidence-chain')
        with open(os.path.join(self.tmp, 'phase141_research_console.html'), 'w') as f:
            f.write('ticker-cards thesis-library evidence-sources daily-delivery')
        with open(os.path.join(self.tmp, 'phase142_ticker_details', 'index.html'), 'w') as f:
            f.write('Research Console detail-page')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_all_pass(self):
        r = check_link_integrity(self.tmp)
        self.assertEqual(r['phase143_link_integrity_check']['overall_status'], 'pass')
        self.assertEqual(r['phase143_link_integrity_check']['files_fail'], 0)

if __name__ == '__main__':
    unittest.main()
