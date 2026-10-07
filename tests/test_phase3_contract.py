import json
import unittest
from pathlib import Path

class Phase3ContractTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_baseline_seed_is_quarantine_only(self):
        text = (self.root / "scripts" / "seed_fiscal_baseline.py").read_text(encoding="utf-8")
        self.assertIn('"_baseline"', text)
        self.assertIn('"public_allowed": "false"', text)
        self.assertNotIn('3_era_modern_2011_2026', text)

    def test_official_hunter_never_promotes_directly(self):
        text = (self.root / "scripts" / "official_evidence_hunter.py").read_text(encoding="utf-8")
        self.assertIn('"promotion_allowed": False', text)
        self.assertIn('DRAFT_OFFICIAL_SOURCE_CANDIDATE', text)

    def test_backfill_policy_forbids_fake_baseline(self):
        text = (self.root / "scripts" / "build_backfill_tasks.py").read_text(encoding="utf-8")
        self.assertIn('MISSING_HISTORY_BECOMES_A_TASK_NOT_A_FAKE_BASELINE', text)

if __name__ == "__main__":
    unittest.main()
