import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ai_hunter_money_parser import primary_money_mention


class MoneyParserTests(unittest.TestCase):
    def test_year_is_not_money(self):
        text = "Jakarta Fair 2026 menargetkan transaksi melampaui Rp8 triliun."
        self.assertEqual(primary_money_mention(text), 8_000_000_000_000)

    def test_bare_year_without_currency_is_not_extracted(self):
        self.assertEqual(primary_money_mention("penerimaan tahun 2026 meningkat"), 0)

    def test_rp_800_juta(self):
        self.assertEqual(primary_money_mention("dugaan suap Rp800 juta"), 800_000_000)


if __name__ == "__main__":
    unittest.main()
