"""Create an atomic, human-review-only content package."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from .exceptions import ReviewPackageError


def _atomic_write(path, content):
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    temporary.replace(path)


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def create_review_package(output_dir, product, template, result, claims_report, now=None):
    if claims_report.get("status") != "PASS":
        raise ReviewPackageError("Пакет нельзя создать: Claims Guard вернул FAIL.")
    now = now or datetime.now()
    folder = Path(output_dir) / f'{now:%Y%m%d-%H%M%S}_{product["id"]}_{template["id"]}'
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise ReviewPackageError(f"Папка результата уже существует: {folder}") from error

    created_at = now.isoformat(timespec="seconds")
    brief = {
        "product": product, "template": template, "created_at": created_at,
        "status": "draft", "requires_manual_review": True,
    }
    metadata = {
        "title": result["title"], "description": result["description"],
        "product_id": result["product_id"], "template_id": result["template_id"],
        "intended_channels": template["intended_channels"], "auto_publish": False,
        "status": "draft",
    }
    facts = "\n".join(f"- {fact}" for fact in result["facts_used"])
    review = f'''# Ручная проверка: {product["name"]}

**Формат:** {template["format"]}

## Сценарий

{result["script"]}

## Проверенные факты

{facts}

## Claims Guard

**Результат:** {claims_report["status"]}

## Чек-лист

- [ ] Проверено название товара
- [ ] Проверена масса упаковки
- [ ] Проверено количество порций
- [ ] Проверена дозировка
- [ ] Проверен объём напитка
- [ ] Проверена страна производства
- [ ] Проверены запрещённые утверждения
- [ ] Проверены визуальные материалы
- [ ] Разрешено публиковать
'''
    files = {
        "brief.json": _json_text(brief), "script.txt": result["script"] + "\n",
        "claims-report.json": _json_text(claims_report), "metadata.json": _json_text(metadata),
        "review.md": review,
    }
    try:
        for name, content in files.items():
            _atomic_write(folder / name, content)
    except OSError as error:
        shutil.rmtree(folder, ignore_errors=True)
        raise ReviewPackageError(f"Не удалось записать пакет: {error}") from error
    return folder.resolve()
