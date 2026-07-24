import json
import tempfile
import unittest
from pathlib import Path

from src.yoku.exceptions import CatalogValidationError, InvalidIdentifierError
from src.yoku.template_catalog import TemplateCatalog


class TemplateCatalogTests(unittest.TestCase):
    def setUp(self):
        self.source = Path("data/templates/ozon-recipe.json")

    def test_valid_template_loads(self):
        self.assertFalse(TemplateCatalog(self.source.parent).load("ozon-recipe")["auto_publish"])

    def _catalog(self, update):
        value = json.loads(self.source.read_text(encoding="utf-8"))
        value.update(update)
        temporary = tempfile.TemporaryDirectory()
        Path(temporary.name, "ozon-recipe.json").write_text(json.dumps(value), encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return TemplateCatalog(temporary.name)

    def test_auto_publish_is_rejected(self):
        with self.assertRaises(CatalogValidationError):
            self._catalog({"auto_publish": True}).load("ozon-recipe")

    def test_manual_review_is_required(self):
        with self.assertRaises(CatalogValidationError):
            self._catalog({"requires_manual_review": False}).load("ozon-recipe")

    def test_bad_duration_is_rejected(self):
        with self.assertRaises(CatalogValidationError):
            self._catalog({"target_duration_seconds": {"min": 20, "max": 15}}).load("ozon-recipe")

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(InvalidIdentifierError):
            TemplateCatalog(self.source.parent).load("../ozon-recipe")

    def test_schema_version_must_be_one(self):
        with self.assertRaises(CatalogValidationError):
            self._catalog({"schema_version": 2}).load("ozon-recipe")

    def test_string_fields_must_be_nonempty(self):
        for field in ("format", "purpose", "language", "hook_template", "cta_template"):
            with self.subTest(field=field):
                with self.assertRaises(CatalogValidationError):
                    self._catalog({field: "   "}).load("ozon-recipe")

    def test_intended_channels_must_be_nonempty_strings(self):
        for value in ([], ["Ozon", ""], "Ozon"):
            with self.subTest(value=value):
                with self.assertRaises(CatalogValidationError):
                    self._catalog({"intended_channels": value}).load("ozon-recipe")

    def test_duration_values_must_be_positive_numbers_not_bool(self):
        for duration in ({"min": True, "max": 20}, {"min": 0, "max": 20}, {"min": 15, "max": False}):
            with self.subTest(duration=duration):
                with self.assertRaises(CatalogValidationError):
                    self._catalog({"target_duration_seconds": duration}).load("ozon-recipe")
