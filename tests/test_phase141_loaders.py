import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_phase140_hardening_loader import load_phase140_hardening
from smr_phase141_phase139_delivery_loader import load_phase139_delivery
from smr_phase141_phase138_thesis_loader import load_phase138_thesis
from smr_phase141_phase134_console_loader import load_phase134_console

class TestLoaders(unittest.TestCase):
    def test_hardening_loader(self):
        r = load_phase140_hardening()
        self.assertEqual(r['phase141_phase140_hardening_loader']['score'], 100)
        self.assertTrue(r['phase141_phase140_hardening_loader']['all_pass'])

    def test_delivery_loader(self):
        r = load_phase139_delivery()
        self.assertTrue(r['phase141_phase139_delivery_loader']['delivery_ready'])

    def test_thesis_loader(self):
        r = load_phase138_thesis()
        self.assertEqual(r['phase141_phase138_thesis_loader']['theses'], 8)

    def test_console_loader(self):
        r = load_phase134_console()
        self.assertTrue(r['phase141_phase134_console_loader']['console_active'])
        self.assertEqual(r['phase141_phase134_console_loader']['ticker_cards'], 8)

if __name__ == '__main__':
    unittest.main()
