import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase201_clean_evidence_store import (
    build_phase201_config,
    build_phase200_loader,
    build_evidence_store_schema,
    build_store_conflict_exclusion_gate,
    build_evidence_records,
    build_store_write_gate,
    build_store_writer,
    build_store_integrity_check,
    build_rollback_package,
    build_300394_evidence_report,
    build_evidence_board,
    build_evidence_brief,
    build_backlog_update,
    build_cannot_conclude_guard,
    build_quality_gate,
    build_dashboard,
    STORE_INPUT_COUNT,
    CLEAN_CANDIDATE_COUNT,
    CONTEXT_CANDIDATE_COUNT
)

class TestPhase201Config(unittest.TestCase):
    def test_config_returns_dict(self):
        r = build_phase201_config()
        self.assertIn('phase201_config', r)
    
    def test_config_store_input_count(self):
        r = build_phase201_config()
        self.assertEqual(r['phase201_config']['store_input_count'], STORE_INPUT_COUNT)
    
    def test_config_packet_disabled(self):
        r = build_phase201_config()
        self.assertTrue(r['phase201_config']['packet_disabled'])
    
    def test_config_watch_core_disabled(self):
        r = build_phase201_config()
        self.assertTrue(r['phase201_config']['watch_core_disabled'])
    
    def test_config_no_mock(self):
        r = build_phase201_config()
        self.assertFalse(r['phase201_config']['mock_used'])

class TestPhase200Loader(unittest.TestCase):
    def test_loader_returns_dict(self):
        r = build_phase200_loader()
        self.assertIn('phase201_phase200_loader', r)
    
    def test_loader_store_ready_count(self):
        r = build_phase200_loader()
        self.assertEqual(r['phase201_phase200_loader']['store_ready_count'], STORE_INPUT_COUNT)
    
    def test_loader_clean_candidates(self):
        r = build_phase200_loader()
        self.assertEqual(r['phase201_phase200_loader']['clean_candidates'], CLEAN_CANDIDATE_COUNT)
    
    def test_loader_context_candidates(self):
        r = build_phase200_loader()
        self.assertEqual(r['phase201_phase200_loader']['context_candidates'], CONTEXT_CANDIDATE_COUNT)
    
    def test_loader_loaded_true(self):
        r = build_phase200_loader()
        self.assertTrue(r['phase201_phase200_loader']['loaded'])

class TestEvidenceStoreSchema(unittest.TestCase):
    def test_schema_version(self):
        r = build_evidence_store_schema()
        self.assertEqual(r['phase201_evidence_store_schema']['schema_version'], '1.0')
    
    def test_schema_has_required_fields(self):
        r = build_evidence_store_schema()
        s = r['phase201_evidence_store_schema']
        self.assertIn('evidence_record_fields', s)
        self.assertIn('direct_evidence_required_fields', s)
        self.assertIn('context_evidence_required_fields', s)
    
    def test_schema_forbidden_fields(self):
        r = build_evidence_store_schema()
        forbidden = r['phase201_evidence_store_schema']['forbidden_in_evidence']
        self.assertIn('buy_signal', forbidden)
        self.assertIn('target_price', forbidden)

class TestConflictExclusionGate(unittest.TestCase):
    def test_conflict_written_zero(self):
        r = build_store_conflict_exclusion_gate()
        self.assertEqual(r['phase201_store_conflict_exclusion_gate']['conflict_items_written_to_store'], 0)
    
    def test_needs_review_written_zero(self):
        r = build_store_conflict_exclusion_gate()
        self.assertEqual(r['phase201_store_conflict_exclusion_gate']['needs_more_review_written_to_store'], 0)
    
    def test_context_as_direct_zero(self):
        r = build_store_conflict_exclusion_gate()
        self.assertEqual(r['phase201_store_conflict_exclusion_gate']['context_as_direct_count'], 0)

class TestEvidenceRecords(unittest.TestCase):
    def test_records_count(self):
        r = build_evidence_records(True)
        self.assertEqual(r['phase201_evidence_records']['total_count'], STORE_INPUT_COUNT)
    
    def test_direct_evidence_count(self):
        r = build_evidence_records(True)
        self.assertEqual(r['phase201_evidence_records']['direct_evidence_count'], CLEAN_CANDIDATE_COUNT)
    
    def test_context_evidence_count(self):
        r = build_evidence_records(True)
        self.assertEqual(r['phase201_evidence_records']['context_evidence_count'], CONTEXT_CANDIDATE_COUNT)
    
    def test_direct_evidence_type(self):
        r = build_evidence_records(True)
        direct = r['phase201_evidence_records']['records'][0]
        self.assertEqual(direct['evidence_type'], 'direct_support_evidence')
        self.assertFalse(direct['is_context_evidence'])
    
    def test_context_evidence_type(self):
        r = build_evidence_records(True)
        ctx = r['phase201_evidence_records']['records'][CLEAN_CANDIDATE_COUNT]
        self.assertEqual(ctx['evidence_type'], 'context_support_evidence')
        self.assertTrue(ctx['is_context_evidence'])
        self.assertTrue(ctx['context_not_direct_marker'])
    
    def test_lineage_complete(self):
        r = build_evidence_records(True)
        self.assertEqual(r['phase201_evidence_records']['lineage_complete'], STORE_INPUT_COUNT)

class TestStoreWriteGate(unittest.TestCase):
    def test_write_gate_false_default(self):
        r = build_store_write_gate(False)
        self.assertFalse(r['phase201_store_write_gate']['can_write'])
    
    def test_write_gate_true(self):
        r = build_store_write_gate(True)
        self.assertTrue(r['phase201_store_write_gate']['can_write'])
    
    def test_write_gate_path_ignored(self):
        r = build_store_write_gate(False)
        self.assertTrue(r['phase201_store_write_gate']['store_path_gitignored'])

class TestStoreWriter(unittest.TestCase):
    def test_writer_no_write_without_flag(self):
        r = build_store_writer(False)
        self.assertFalse(r['phase201_store_writer']['store_written'])
        self.assertEqual(r['phase201_store_writer']['reason'], 'write_store_flag_not_provided')
    
    def test_writer_with_flag(self):
        r = build_store_writer(True)
        self.assertTrue(r['phase201_store_writer']['store_written'])
        self.assertEqual(r['phase201_store_writer']['direct_evidence_written'], CLEAN_CANDIDATE_COUNT)
        self.assertEqual(r['phase201_store_writer']['context_evidence_written'], CONTEXT_CANDIDATE_COUNT)
        self.assertEqual(r['phase201_store_writer']['total_evidence_written'], STORE_INPUT_COUNT)
    
    def test_writer_conflict_zero(self):
        r = build_store_writer(True)
        self.assertEqual(r['phase201_store_writer']['conflict_written'], 0)
    
    def test_writer_context_as_direct_zero(self):
        r = build_store_writer(True)
        self.assertEqual(r['phase201_store_writer']['context_as_direct'], 0)

class TestStoreIntegrity(unittest.TestCase):
    def test_integrity_pass(self):
        r = build_store_integrity_check(False)
        self.assertTrue(r['phase201_store_integrity_check']['integrity_pass'])
    
    def test_integrity_no_duplicates(self):
        r = build_store_integrity_check(False)
        self.assertEqual(r['phase201_store_integrity_check']['duplicate_count'], 0)
    
    def test_integrity_no_forbidden(self):
        r = build_store_integrity_check(True)
        self.assertTrue(r['phase201_store_integrity_check']['no_forbidden_fields'])

class TestRollback(unittest.TestCase):
    def test_rollback_generated(self):
        r = build_rollback_package(False)
        self.assertTrue(r['phase201_rollback_package']['rollback_package_generated'])
    
    def test_rollback_safety(self):
        r = build_rollback_package(True)
        self.assertIn('no_packet_or_watch_core_affected', r['phase201_rollback_package']['rollback_safety'])

class Test300394Report(unittest.TestCase):
    def test_cninfo_retained(self):
        r = build_300394_evidence_report(False)
        self.assertTrue(r['phase201_300394_evidence_report']['300394_cninfo_limitation_retained'])

class TestEvidenceBoard(unittest.TestCase):
    def test_board_generated(self):
        r = build_evidence_board(False)
        self.assertTrue(r['phase201_evidence_board']['board_generated'])
    
    def test_board_sections(self):
        r = build_evidence_board(False)
        sections = r['phase201_evidence_board']['sections']
        self.assertEqual(len(sections['direct_evidence']), CLEAN_CANDIDATE_COUNT)
        self.assertEqual(len(sections['context_evidence']), CONTEXT_CANDIDATE_COUNT)

class TestEvidenceBrief(unittest.TestCase):
    def test_brief_generated(self):
        r = build_evidence_brief(False)
        self.assertTrue(r['phase201_evidence_brief']['brief_generated'])
    
    def test_brief_not_trade_advice(self):
        r = build_evidence_brief(False)
        self.assertTrue(r['phase201_evidence_brief']['brief_not_trade_advice'])

class TestBacklog(unittest.TestCase):
    def test_backlog_generated(self):
        r = build_backlog_update(False)
        self.assertTrue(r['phase201_backlog_update']['backlog_generated'])

class TestGuard(unittest.TestCase):
    def test_guard_pass_default(self):
        r = build_cannot_conclude_guard(False)
        self.assertTrue(r['phase201_cannot_conclude_guard']['guard_pass'])
    
    def test_guard_violations_zero(self):
        r = build_cannot_conclude_guard(False)
        self.assertEqual(r['phase201_cannot_conclude_guard']['violations_count'], 0)

class TestQualityGate(unittest.TestCase):
    def test_gate_pass(self):
        r = build_quality_gate(False)
        self.assertTrue(r['phase201_quality_gate']['gate_pass'])
    
    def test_gate_no_failed_checks(self):
        r = build_quality_gate(True)
        self.assertEqual(len(r['phase201_quality_gate']['failed_checks']), 0)

class TestDashboard(unittest.TestCase):
    def test_dashboard_generated(self):
        r = build_dashboard(False)
        self.assertTrue(r['phase201_dashboard']['dashboard_generated'])
    
    def test_dashboard_safety(self):
        r = build_dashboard(True)
        s = r['phase201_dashboard']['safety']
        self.assertFalse(s['mock_used'])
        self.assertFalse(s['fixture_used'])
        self.assertFalse(s['trade_recommendation_created'])
        self.assertFalse(s['broker_api_called'])

if __name__ == '__main__':
    unittest.main()
