"""Load and validate trusted product cards from a local JSON catalog."""

import json
import re
from pathlib import Path

from .exceptions import (
    CatalogItemNotFoundError,
    CatalogValidationError,
    InvalidIdentifierError,
)

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = {
    "schema_version", "id", "brand", "name", "category", "package_weight_g",
    "servings", "dosage_g_per_drink", "drink_volume_ml", "country_of_origin",
    "audience", "positioning", "allowed_claims", "prohibited_claims",
}
NUMERIC_FIELDS = ("package_weight_g", "servings", "dosage_g_per_drink", "drink_volume_ml")


def _validate_id(item_id):
    if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id):
        raise InvalidIdentifierError(
            "Идентификатор должен содержать только строчные латинские буквы, цифры и дефисы."
        )


def _positive_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


class ProductCatalog:
    def __init__(self, directory):
        self.directory = Path(directory)

    def load(self, product_id):
        _validate_id(product_id)
        path = self.directory / f"{product_id}.json"
        if not path.is_file():
            raise CatalogItemNotFoundError(f"Карточка товара не найдена: {product_id}")
        try:
            with path.open("r", encoding="utf-8") as stream:
                product = json.load(stream)
        except (json.JSONDecodeError, OSError) as error:
            raise CatalogValidationError(f"Не удалось прочитать карточку {product_id}: {error}") from error
        if not isinstance(product, dict):
            raise CatalogValidationError("Карточка товара должна быть JSON-объектом.")
        missing = sorted(REQUIRED_FIELDS - product.keys())
        if missing:
            raise CatalogValidationError(f"В карточке отсутствуют поля: {', '.join(missing)}")
        if product["id"] != product_id:
            raise CatalogValidationError("ID внутри карточки не совпадает с именем файла.")
        if product["schema_version"] != 1:
            raise CatalogValidationError("Поддерживается schema_version=1.")
        for field in NUMERIC_FIELDS:
            if not _positive_number(product[field]):
                raise CatalogValidationError(f"Поле {field} должно быть положительным числом.")
        for field in ("allowed_claims", "prohibited_claims"):
            value = product[field]
            if not isinstance(value, list) or not value or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                raise CatalogValidationError(f"Поле {field} должно быть непустым списком строк.")
        return product


def load_product(product_id, directory):
    return ProductCatalog(directory).load(product_id)
