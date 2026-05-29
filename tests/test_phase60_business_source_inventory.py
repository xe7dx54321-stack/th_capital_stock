import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_business_source_inventory import build_business_source_inventory
class T(unittest.TestCase):
    def test_sources(self): r=build_business_source_inventory(); self.assertGreater(r['business_source_inventory']['sources_checked'],0)
    def test_no_raw(self): r=build_business_source_inventory(); self.assertFalse(r['business_source_inventory']['raw_content_saved'])
    def test_no_ocr(self): r=build_business_source_inventory(); self.assertFalse(r['business_source_inventory']['ocr_used'])
if __name__=='__main__': unittest.main()
