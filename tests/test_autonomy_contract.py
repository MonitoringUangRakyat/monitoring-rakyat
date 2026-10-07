import json
import unittest
from pathlib import Path

class AutonomyContractTests(unittest.TestCase):
    def test_registry_has_four_official_sources(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"config/official_source_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["sources"]),4)
        self.assertTrue(all(x["authority"] >= 90 for x in data["sources"]))

    def test_official_urls_are_https(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"config/official_source_registry.json").read_text(encoding="utf-8"))
        for src in data["sources"]:
            for url in src["candidate_urls"]:
                self.assertTrue(url.startswith("https://"))

if __name__=="__main__":
    unittest.main()
