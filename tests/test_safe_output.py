import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT/"08_scripts"/"lib", ROOT/"08_scripts"/"reporting", ROOT/"08_scripts"/"verification", ROOT/"tests"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))

import unittest
from smr_safe_output import safe_print, safe_print_json

class TestSafeOutput(unittest.TestCase):
    def test_safe_print_normal(self):
        safe_print("hello world")
    def test_safe_print_unicode(self):
        safe_print("test \u4e2d\u6587")
    def test_safe_print_special_char(self):
        safe_print("test \uf052")
    def test_safe_print_json_normal(self):
        safe_print_json({"a": 1, "b": "hello"})
    def test_safe_print_json_unicode(self):
        safe_print_json({"ticker": "300308.SZ", "name": "\u4e2d\u9645\u65ed\u521b"})

if __name__ == "__main__": unittest.main()
