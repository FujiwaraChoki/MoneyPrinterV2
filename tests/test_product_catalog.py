import json
import tempfile
import unittest
from pathlib import Path

from src.yoku.exceptions import CatalogValidationError, InvalidIdentifierError
from src.yoku.product_catalog import ProductCatalog


class ProductCatalogTests(unittest.TestCase):
    def setUp(self):
        self.source = Path("data/products/taro-100g.json")

    def test_valid_product_loads(self):
        self.assertEqual(ProductCatalog(self.source.parent).load("taro-100g")["servings"], 5)

    def _invalid_copy(self, update=None, remove=None):
        product = json.loads(self.source.read_text(encoding="utf-8"))
        if update:
            product.update(update)
        if remove:
            product.pop(remove)
        temporary = tempfile.TemporaryDirectory()
        Path(temporary.name, "taro-100g.json").write_text(json.dumps(product), encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return ProductCatalog(temporary.name)

    def test_missing_field_is_rejected(self):
        with self.assertRaises(CatalogValidationError):
            self._invalid_copy(remove="brand").load("taro-100g")

    def test_wrong_numeric_type_is_rejected(self):
        with self.assertRaises(CatalogValidationError):
            self._invalid_copy({"servings": "5"}).load("taro-100g")

    def test_mismatched_id_is_rejected(self):
        with self.assertRaises(CatalogValidationError):
            self._invalid_copy({"id": "other"}).load("taro-100g")

    def test_path_traversal_is_rejected(self):
        for value in ("../taro-100g", "/tmp/item", "item.json", "item\\other"):
            with self.subTest(value=value), self.assertRaises(InvalidIdentifierError):
                ProductCatalog(self.source.parent).load(value)
