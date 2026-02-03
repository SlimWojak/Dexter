"""Model diversity test — verify cross-family veto pattern."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.router import _load_role, clear_cache


class TestModelDiversity(unittest.TestCase):
    """Theorist and Auditor must use different model families."""

    @classmethod
    def setUpClass(cls):
        clear_cache()
        cls.theorist = _load_role("theorist")
        cls.auditor = _load_role("auditor")

    def test_theorist_is_deepseek(self):
        self.assertEqual(self.theorist.get("family"), "deepseek")

    def test_auditor_is_google(self):
        self.assertEqual(self.auditor.get("family"), "google")

    def test_families_are_different(self):
        """Cross-family veto: Theorist and Auditor MUST be different families."""
        t_family = self.theorist.get("family")
        a_family = self.auditor.get("family")
        self.assertNotEqual(
            t_family, a_family,
            f"Model family collision: both are '{t_family}'. Cross-family veto violated.",
        )

    def test_theorist_model_specified(self):
        self.assertTrue(self.theorist.get("model"))

    def test_auditor_model_specified(self):
        self.assertTrue(self.auditor.get("model"))

    def test_theorist_provider_is_openrouter(self):
        self.assertEqual(self.theorist.get("provider"), "openrouter")

    def test_auditor_provider_is_openrouter(self):
        self.assertEqual(self.auditor.get("provider"), "openrouter")


if __name__ == "__main__":
    unittest.main()
