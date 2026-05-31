import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBandClassifier(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_band_classifier_report import build;r=build();b=r["phase85_valuation_band_classifier"];self.assertGreater(b["bands_created"],0)
    def test_band_mix_has_keys(self):from build_phase85_valuation_band_classifier_report import build;r=build();b=r["phase85_valuation_band_classifier"];self.assertGreater(len(b["band_mix"]),0)
if __name__=="__main__":unittest.main()
