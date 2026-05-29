import unittest, sys; sys.path.insert(0,'08_scripts/lib')
from smr_ai_optical_business_variable_schema import get_business_variables, build_business_schema_report
class T(unittest.TestCase):
    def test_7_vars(self): self.assertGreaterEqual(len(get_business_variables()),7)
    def test_cannot_conclude(self):
        for v in get_business_variables(): self.assertGreater(len(v.get('cannot_conclude_without_direct_disclosure',[])),0)
    def test_report(self): self.assertGreater(build_business_schema_report()['variables_count'],0)
if __name__=='__main__': unittest.main()
