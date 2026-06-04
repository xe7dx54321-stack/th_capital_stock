import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase160Config(unittest.TestCase):
    def test_config(self):
        from smr_phase160_config import load_phase160_config
        c = load_phase160_config()
        self.assertEqual(c["phase"], "phase160")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["owner_decision_example_pack_enabled"])
        self.assertTrue(c["safe_input_sandbox_enabled"])
        self.assertTrue(c["sandbox_validation_enabled"])
        self.assertFalse(c["real_owner_input_write_allowed"])
        self.assertFalse(c["real_owner_input_overwrite_allowed"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertTrue(c["simulation_only"])
        self.assertFalse(c["llm_api_enabled"])
        self.assertFalse(c["broker_integration_allowed"])

class TestPhase160DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase160_domain_registry import build_phase160_domain_registry
        r = build_phase160_domain_registry()
        dr = r["phase160_domain_registry"]
        self.assertEqual(len(dr["domains"]), 3)
        self.assertFalse(dr["mock_used"])

class TestPhase160Schema(unittest.TestCase):
    def test_schema(self):
        from smr_phase160_example_schema import build_example_schema
        s = build_example_schema()
        schema = s["phase160_example_schema"]
        self.assertIn("example_id", schema["required_fields"])
        self.assertIn("input_json", schema["required_fields"])
        self.assertEqual(len(schema["allowed_decisions"]), 5)
        self.assertGreater(len(schema["forbidden_fields"]), 0)

class TestPhase160Generators(unittest.TestCase):
    def test_all_examples_generated(self):
        from smr_phase160_generators import generate_all_examples
        pack = generate_all_examples()
        p = pack["phase160_example_pack"]
        self.assertEqual(p["total_examples"], 10)
        self.assertEqual(p["valid_examples"], 5)
        self.assertEqual(p["invalid_examples"], 5)
        self.assertEqual(len(p["examples"]), 10)

    def test_valid_examples(self):
        from smr_phase160_generators import generate_all_examples
        pack = generate_all_examples()
        examples = pack["phase160_example_pack"]["examples"]
        valid = [e for e in examples if e["is_valid_example"]]
        self.assertEqual(len(valid), 5)
        for e in valid:
            self.assertTrue(e["expected_safe_count"] > 0)
            self.assertEqual(e["expected_invalid_count"], 0)
            self.assertEqual(e["expected_quarantine_count"], 0)
            self.assertEqual(e["expected_execution_count"], 0)

    def test_invalid_examples(self):
        from smr_phase160_generators import generate_all_examples
        pack = generate_all_examples()
        examples = pack["phase160_example_pack"]["examples"]
        invalid = [e for e in examples if not e["is_valid_example"]]
        self.assertEqual(len(invalid), 5)
        for e in invalid:
            self.assertTrue(e["expected_invalid_count"] > 0)
            self.assertEqual(e["expected_execution_count"], 0)

    def test_trade_like_example(self):
        from smr_phase160_generators import generate_invalid_trade_like_example
        ex = generate_invalid_trade_like_example()
        self.assertTrue(ex["is_trade_like"])
        self.assertFalse(ex["is_valid_example"])
        rationale = ex["input_json"]["decisions"][0]["rationale"].lower()
        self.assertIn("buy", rationale)

    def test_example_schema_compliance(self):
        from smr_phase160_generators import generate_all_examples
        pack = generate_all_examples()
        for ex in pack["phase160_example_pack"]["examples"]:
            self.assertIn("example_id", ex)
            self.assertIn("example_name", ex)
            self.assertIn("input_json", ex)
            self.assertIn("decisions", ex["input_json"])
            for d in ex["input_json"]["decisions"]:
                self.assertIn("ticker", d)
                self.assertIn("decision", d)
                self.assertIn("rationale", d)

class TestPhase160Sandbox(unittest.TestCase):
    def test_sandbox_valid_example(self):
        from smr_phase160_generators import generate_all_examples
        from smr_phase160_sandbox import run_sandbox_validation
        pack = generate_all_examples()
        valid = [e for e in pack["phase160_example_pack"]["examples"] if e["is_valid_example"]][0]
        r = run_sandbox_validation(valid)
        v = r["phase160_sandbox_validation"]
        self.assertEqual(v["invalid_count"], 0)
        self.assertEqual(v["quarantine_count"], 0)
        self.assertTrue(v["sandbox_not_execution"])

    def test_sandbox_trade_like_quarantine(self):
        from smr_phase160_generators import generate_invalid_trade_like_example
        from smr_phase160_sandbox import run_sandbox_validation
        ex = generate_invalid_trade_like_example()
        r = run_sandbox_validation(ex)
        v = r["phase160_sandbox_validation"]
        self.assertTrue(v["invalid_count"] > 0)
        self.assertTrue(v["quarantine_count"] > 0)
        self.assertTrue(v["sandbox_not_execution"])

    def test_sandbox_unknown_candidate(self):
        from smr_phase160_generators import generate_unknown_candidate_example
        from smr_phase160_sandbox import run_sandbox_validation
        ex = generate_unknown_candidate_example()
        r = run_sandbox_validation(ex)
        v = r["phase160_sandbox_validation"]
        self.assertTrue(v["invalid_count"] > 0)

    def test_sandbox_aggregation(self):
        from smr_phase160_generators import generate_all_examples
        from smr_phase160_sandbox import run_sandbox_validation, aggregate_sandbox_results
        pack = generate_all_examples()
        examples = pack["phase160_example_pack"]["examples"]
        results = [run_sandbox_validation(e) for e in examples]
        agg = aggregate_sandbox_results(results)
        a = agg["phase160_sandbox_aggregator"]
        self.assertEqual(a["total_examples"], 10)
        self.assertEqual(a["total_execution"], 0)

class TestPhase160Expectations(unittest.TestCase):
    def test_expectations_all_match(self):
        from smr_phase160_generators import generate_all_examples
        from smr_phase160_sandbox import run_sandbox_validation
        from smr_phase160_expectation_checker import check_all_expectations
        pack = generate_all_examples()
        examples = pack["phase160_example_pack"]["examples"]
        results = [run_sandbox_validation(e) for e in examples]
        ec = check_all_expectations(examples, results)
        self.assertTrue(ec["phase160_expectation_checker_aggregate"]["all_expectations_match"])

class TestPhase160Compatibility(unittest.TestCase):
    def test_compatibility(self):
        from smr_phase160_compatibility_checker import check_phase159_compatibility
        r = check_phase159_compatibility()
        self.assertTrue(r["phase160_compatibility_checker"]["phase159_compatible"])

class TestPhase160Guard(unittest.TestCase):
    def test_guard_pass(self):
        from smr_phase160_guard import build_sandbox_guard
        g = build_sandbox_guard()
        self.assertEqual(g["phase160_sandbox_guard"]["status"], "pass")
        self.assertEqual(g["phase160_sandbox_guard"]["violations"], 0)

class TestPhase160QualityGate(unittest.TestCase):
    def test_quality_gate_pass(self):
        from smr_phase160_quality_gate import build_quality_gate
        q = build_quality_gate()
        self.assertEqual(q["phase160_quality_gate"]["status"], "pass")

class TestPhase160CannotConclude(unittest.TestCase):
    def test_cannot_conclude_pass(self):
        from smr_phase160_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase160_cannot_conclude_guard"]["status"], "pass")
        self.assertEqual(cc["phase160_cannot_conclude_guard"]["violations"], 0)
        self.assertIn("300394 CNINFO org_id missing", cc["phase160_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase160Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase160_example_pack_pipeline import run
        r = run("dry-run")
        p = r["phase160_example_pack_pipeline"]
        self.assertEqual(p["total_examples"], 10)
        self.assertEqual(p["sandbox_total_execution"], 0)
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["cannot_conclude_guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["example_pack_generated"])
        self.assertTrue(p["expectations_all_match"])
        self.assertTrue(p["phase159_compatible"])
        self.assertFalse(p["real_owner_input_overwritten"])
        self.assertFalse(p["watch_core_updated"])
        self.assertFalse(p["activation_execution_created"])
        self.assertEqual(p["mock_used"], False)
        self.assertEqual(p["fixture_used"], False)
        self.assertEqual(p["pending_created"], 0)
        self.assertEqual(p["paper_order_created"], 0)
        self.assertEqual(p["real_trade_created"], 0)

    def test_execute(self):
        from run_phase160_example_pack_pipeline import run
        r = run("execute")
        p = r["phase160_example_pack_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["mock_used"], False)

    def test_skip_network(self):
        from run_phase160_example_pack_pipeline import run
        r = run("skip-network")
        p = r["phase160_example_pack_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
