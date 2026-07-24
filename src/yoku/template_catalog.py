"""Load and validate safe local content templates."""

import json
from pathlib import Path

from .exceptions import CatalogItemNotFoundError, CatalogValidationError
from .product_catalog import _validate_id

REQUIRED_FIELDS = {
    "schema_version", "id", "format", "purpose", "language", "hook_template",
    "scene_templates", "cta_template", "target_duration_seconds",
    "requires_manual_review", "auto_publish", "intended_channels",
}


class TemplateCatalog:
    def __init__(self, directory):
        self.directory = Path(directory)

    def load(self, template_id):
        _validate_id(template_id)
        path = self.directory / f"{template_id}.json"
        if not path.is_file():
            raise CatalogItemNotFoundError(f"Шаблон не найден: {template_id}")
        try:
            with path.open("r", encoding="utf-8") as stream:
                template = json.load(stream)
        except (json.JSONDecodeError, OSError) as error:
            raise CatalogValidationError(f"Не удалось прочитать шаблон {template_id}: {error}") from error
        if not isinstance(template, dict):
            raise CatalogValidationError("Шаблон должен быть JSON-объектом.")
        missing = sorted(REQUIRED_FIELDS - template.keys())
        if missing:
            raise CatalogValidationError(f"В шаблоне отсутствуют поля: {', '.join(missing)}")
        if template["id"] != template_id:
            raise CatalogValidationError("ID внутри шаблона не совпадает с именем файла.")
        if template["schema_version"] != 1:
            raise CatalogValidationError("schema_version шаблона должен быть равен 1.")
        for field in ("format", "purpose", "language", "hook_template", "cta_template"):
            if not isinstance(template[field], str) or not template[field].strip():
                raise CatalogValidationError(f"Поле {field} должно быть непустой строкой.")
        channels = template["intended_channels"]
        if not isinstance(channels, list) or not channels or not all(isinstance(channel, str) and channel.strip() for channel in channels):
            raise CatalogValidationError("intended_channels должен быть непустым списком непустых строк.")
        duration = template["target_duration_seconds"]
        if (
            not isinstance(duration, dict)
            or set(("min", "max")) - duration.keys()
            or not all(isinstance(duration[key], (int, float)) and not isinstance(duration[key], bool) for key in ("min", "max"))
            or duration["min"] <= 0
            or duration["min"] >= duration["max"]
        ):
            raise CatalogValidationError("Длительность должна содержать положительные min и max, где min < max.")
        scenes = template["scene_templates"]
        if not isinstance(scenes, list) or not scenes or not all(isinstance(scene, str) and scene.strip() for scene in scenes):
            raise CatalogValidationError("scene_templates должен быть непустым списком строк.")
        if template["requires_manual_review"] is not True:
            raise CatalogValidationError("Для шаблона обязательно ручное согласование.")
        if template["auto_publish"] is not False:
            raise CatalogValidationError("Автоматическая публикация должна быть отключена.")
        return template


def load_template(template_id, directory):
    return TemplateCatalog(directory).load(template_id)
