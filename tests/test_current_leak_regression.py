import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evidence_policy import is_publishable_record, loss_amount, parse_money


class CurrentLeakRegressionTests(unittest.TestCase):
    def setUp(self):
        base = {
            "Status_Hukum": "DRAFT_REVIEW_NEEDS_OFFICIAL_EVIDENCE",
            "Status_Verifikasi": "AI_HUNTER_DRAFT_REVIEW",
            "Sumber_Perhitungan": "CNN Indonesia",
            "Link_Referensi": "https://example.test/media",
        }
        self.rows = [
            {**base, "Kasus": "case1", "Nilai_Kerugian": "Rp 800.000.000", "Kerugian": "Rp 800.000.000"},
            {**base, "Kasus": "case2", "Nilai_Kerugian": "", "Kerugian": ""},
            {**base, "Kasus": "case3", "Nilai_Kerugian": "Rp 56.000.000.000", "Kerugian": "Rp 56.000.000.000"},
            {**base, "Kasus": "case4", "Nilai_Kerugian": "", "Kerugian": ""},
            {**base, "Kasus": "case5", "Nilai_Kerugian": "Rp 7.000.000.000", "Kerugian": "Rp 7.000.000.000"},
        ]

    def test_legacy_double_count_reproduces_127_6b(self):
        legacy = sum(parse_money(r.get("Nilai_Kerugian")) + parse_money(r.get("Kerugian")) for r in self.rows)
        self.assertEqual(legacy, 127_600_000_000)

    def test_canonical_amount_is_63_8b_before_gate(self):
        self.assertEqual(sum(loss_amount(r) for r in self.rows), 63_800_000_000)

    def test_all_drafts_are_quarantined(self):
        publishable = [r for r in self.rows if is_publishable_record(r)]
        self.assertEqual(publishable, [])


if __name__ == "__main__":
    unittest.main()
