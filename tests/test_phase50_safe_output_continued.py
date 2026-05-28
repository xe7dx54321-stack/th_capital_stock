import unittest, sys; from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/'08_scripts'/'lib',ROOT/'tests'):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from smr_safe_output import safe_print_json
class Phase50SafeOutputTests(unittest.TestCase):
    def test_safe_print(self): safe_print_json({'ticker':'300308.SZ','text':'test \u4e2d\u6587'})
    def test_unicode_special(self): safe_print_json({'char':'\uf052','desc':'test'})
if __name__=='__main__': unittest.main()
