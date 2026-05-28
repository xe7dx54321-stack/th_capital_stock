import unittest, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT/'08_scripts'/'verification', ROOT/'08_scripts'/'lib', ROOT/'tests'):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
from smr_safe_output import safe_print_json
class Phase49SafeOutputWiringTests(unittest.TestCase):
    def test_safe_print_json_unicode(self):
        safe_print_json({'ticker':'300308.SZ','name':'\u4e2d\u9645\u65ed\u521b','status':'\u8ddf\u8e2a\u4e2d'})
    def test_safe_print_json_special_char(self):
        safe_print_json({'symbol':'\uf052','value':100})
    def test_safe_print_json_large_dict(self):
        safe_print_json({'a':1,'b':'hello','c':[1,2,3],'d':{'nested':True}})
if __name__=='__main__': unittest.main()
