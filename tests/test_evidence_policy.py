import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evidence_policy import is_publishable_record, loss_amount, publication_decision


class EvidencePolicyTests(unittest.TestCase):
    def test_draft_with_media_source_is_blocked(self):
        row = {
            "Status_Hukum": "DRAFT_REVIEW_NEEDS_OFFICIAL_EVIDENCE",
            "Status_Verifikasi": "AI_HUNTER_DRAFT_REVIEW",
            "Sumber_Perhitungan": "CNN Indonesia",
            "Link_Referensi": "https://example.test/story",
            "Kerugian": "Rp 56.000.000.000",
        }
        self.assertFalse(is_publishable_record(row))
        self.assertEqual(publication_decision(row).reason, "blocked_status")

    def test_verified_source_with_evidence_is_allowed(self):
        row = {"Status_Verifikasi": "VERIFIED_SOURCE", "Link_Referensi": "https://official.example/doc", "Kerugian": "Rp 1 miliar"}
        self.assertTrue(is_publishable_record(row))

    def test_verified_without_source_is_blocked(self):
        row = {"Status_Verifikasi": "VERIFIED_SOURCE", "Kerugian": "Rp 1 miliar"}
        self.assertFalse(is_publishable_record(row))
        self.assertEqual(publication_decision(row).reason, "missing_source")

    def test_money_aliases_do_not_double_count(self):
        row = {"Nilai_Kerugian": "Rp 56.000.000.000", "Kerugian": "Rp 56.000.000.000"}
        self.assertEqual(loss_amount(row), 56_000_000_000)


if __name__ == "__main__":
    unittest.main()
