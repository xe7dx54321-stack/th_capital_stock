import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestHTMLUtils(unittest.TestCase):
 def test_remove_scripts(self):
  from smr_phase74_html_parser_utils import remove_scripts_styles
  h="<html><script>alert(1)</script><p>text</p><style>.a{}</style></html>";r=remove_scripts_styles(h)
  self.assertNotIn("alert",r);self.assertNotIn(".a{}",r);self.assertIn("text",r)
 def test_extract_visible_text(self):
  from smr_phase74_html_parser_utils import extract_visible_text
  r=extract_visible_text("<p>Hello World</p>")
  self.assertIn("Hello World",r)
 def test_extract_links(self):
  from smr_phase74_html_parser_utils import extract_links
  r=extract_links("<a href=\"/page\">Link</a>","https://example.com")
  self.assertTrue(any("example.com/page" in l["url"] for l in r))
 def test_detect_pdf(self):
  from smr_phase74_html_parser_utils import detect_pdf_links
  r=detect_pdf_links([{"url":"a.pdf","anchor_text":""},{"url":"b.html","anchor_text":""}])
  self.assertEqual(len(r),1);self.assertIn("a.pdf",r[0]["url"])
 def test_text_hash_stable(self):
  from smr_phase74_html_parser_utils import text_hash
  h1=text_hash("test");h2=text_hash("test")
  self.assertEqual(h1,h2)
 def test_remove_boilerplate(self):
  from smr_phase74_html_parser_utils import remove_boilerplate
  r=remove_boilerplate("Hello\nCopyright 2024\nWorld\n备案号123")
  self.assertNotIn("Copyright",r);self.assertNotIn("备案号",r);self.assertIn("Hello",r)
if __name__=="__main__":unittest.main()
