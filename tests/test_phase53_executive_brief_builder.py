import phase53_helpers, unittest; from smr_executive_brief_builder import build_executive
class Phase53ExecBriefTests(unittest.TestCase):
    def test_has_conclusion(self):
        r=build_executive("300308.SZ"); eb=r["executive_brief"]
        self.assertGreater(len(eb.get("conclusion",[])),0)
    def test_no_long(self):
        r=build_executive("300308.SZ"); eb=r["executive_brief"]
        for k in ["conclusion","changes","support","blockers","next_steps"]:
            items=eb.get(k,[]); self.assertLessEqual(len(items),5)
    def test_forbidden_note_present(self):
        r=build_executive("300308.SZ")
        self.assertIn("forbidden_note",r["executive_brief"])
if __name__=="__main__": unittest.main()
