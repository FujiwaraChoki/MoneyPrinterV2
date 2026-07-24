import unittest

from src.yoku.claims_guard import check_claims
from src.yoku.product_catalog import ProductCatalog


class ClaimsGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = ProductCatalog("data/products").load("taro-100g")

    def test_valid_script_passes(self):
        text = "5 порций. 100 г смеси. По 20 г на напиток объёмом 300 мл. Произведено в Тайване."
        self.assertEqual(check_claims(text, self.product)["status"], "PASS")

    def test_every_prohibited_phrase_fails(self):
        for phrase in self.product["prohibited_claims"]:
            with self.subTest(phrase=phrase):
                self.assertEqual(check_claims(phrase, self.product)["status"], "FAIL")

    def test_prohibited_phrase_ignores_case_and_spaces(self):
        report = check_claims("БЕЗ     САХАРА", self.product)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("position", report["errors"][0])

    def test_incorrect_numeric_facts_fail(self):
        for text in ("200 г в упаковке", "7 порций", "28 г на напиток", "напиток объёмом 400 мл"):
            with self.subTest(text=text):
                self.assertEqual(check_claims(text, self.product)["status"], "FAIL")

    def test_package_weight_contexts_fail(self):
        for text in (
            "200 г в упаковке",
            "200 г смеси",
            "упаковка 200 г",
            "масса упаковки 200 г",
            "в упаковке 200 граммов",
        ):
            with self.subTest(text=text):
                report = check_claims(text, self.product)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(report["errors"][0]["field"], "package_weight_g")

    def test_drink_volume_contexts_are_relevant(self):
        fail_report = check_claims("напиток объёмом 400 мл", self.product)
        self.assertEqual(fail_report["status"], "FAIL")
        self.assertEqual(fail_report["errors"][0]["field"], "drink_volume_ml")

        water_report = check_claims("Добавьте 50 мл воды.", self.product)
        self.assertNotIn("drink_volume_ml", [error.get("field") for error in water_report["errors"]])

        self.assertEqual(check_claims("напиток объёмом 300 мл", self.product)["status"], "PASS")

    def test_other_country_fails(self):
        self.assertEqual(check_claims("Смесь произведена в России.", self.product)["status"], "FAIL")

    def test_unrelated_numbers_are_not_product_facts(self):
        self.assertEqual(check_claims("Ролик длится 20 секунд.", self.product)["status"], "PASS")
