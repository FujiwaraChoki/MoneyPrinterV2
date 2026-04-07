import re


STAGE_NAMES = ("research", "product_spec", "design_system", "page_blueprint", "render", "mockups", "listing_package")
VALID_CATEGORIES = {"planner", "tracker", "worksheet"}
VALID_RUN_STATUSES = {"in_progress", "failed", "completed"}
VALID_TEMPLATE_FAMILIES = {"clean-minimal", "dark-luxury", "cottagecore", "bold-playful"}
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _require_relative_path(payload: dict, field_name: str, suffix: str | None = None) -> str:
    value = payload.get(field_name, "")
    if not isinstance(value, str) or not value:
        raise ValueError(field_name)
    if value.startswith("/"):
        raise ValueError(field_name)
    if suffix and not value.endswith(suffix):
        raise ValueError(field_name)
    return value


def validate_research_artifact(payload: dict) -> dict:
    required_fields = {"run_id", "category", "opportunities", "selected_opportunity"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing research fields: {sorted(missing)}")

    if payload["category"] not in VALID_CATEGORIES:
        raise ValueError("category")

    opportunities = payload["opportunities"]
    if not isinstance(opportunities, list) or not opportunities:
        raise ValueError("opportunities")

    idea_slugs = {item.get("idea_slug") for item in opportunities}
    if payload["selected_opportunity"] not in idea_slugs:
        raise ValueError("selected_opportunity")

    return payload


def validate_product_spec_artifact(payload: dict) -> dict:
    required_fields = {
        "run_id",
        "product_type",
        "audience",
        "title_theme",
        "page_count",
        "page_size",
        "sections",
        "style_notes",
        "output_files",
    }
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing product spec fields: {sorted(missing)}")

    if not isinstance(payload["page_count"], int) or payload["page_count"] <= 0:
        raise ValueError("page_count")

    if not isinstance(payload["sections"], list) or not payload["sections"]:
        raise ValueError("sections")

    accent_color = payload["style_notes"].get("accent_color", "")
    if not HEX_COLOR_RE.match(accent_color):
        raise ValueError("accent_color")

    return payload


def validate_run_status(payload: dict) -> dict:
    required_fields = {
        "run_id",
        "status",
        "current_stage",
        "last_successful_stage",
        "failure_message",
    }
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing run status fields: {sorted(missing)}")

    if payload["status"] not in VALID_RUN_STATUSES:
        raise ValueError("status")

    return payload


def validate_design_system_artifact(payload: dict) -> dict:
    required_fields = {"run_id", "palette", "typography", "layout", "mockup_style"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing design system fields: {sorted(missing)}")

    palette = payload["palette"]
    if not isinstance(palette, dict):
        raise ValueError("palette")
    for field_name in ("primary", "secondary", "background"):
        color = palette.get(field_name, "")
        if not HEX_COLOR_RE.match(color):
            raise ValueError("palette")

    typography = payload["typography"]
    if not isinstance(typography, dict):
        raise ValueError("typography")
    for field_name in ("heading_font", "body_font"):
        if not isinstance(typography.get(field_name), str) or not typography[field_name].strip():
            raise ValueError("typography")

    layout = payload["layout"]
    if not isinstance(layout, dict):
        raise ValueError("layout")
    for field_name in ("template_name", "header_style", "page_frame_style"):
        if not isinstance(layout.get(field_name), str) or not layout[field_name].strip():
            raise ValueError("layout")
    template_family = layout.get("template_family", "clean-minimal")
    if template_family not in VALID_TEMPLATE_FAMILIES:
        raise ValueError("template_family")

    mockup_style = payload["mockup_style"]
    if not isinstance(mockup_style, dict):
        raise ValueError("mockup_style")
    background_color = mockup_style.get("background_color", "")
    if not HEX_COLOR_RE.match(background_color):
        raise ValueError("mockup_style")
    if not isinstance(mockup_style.get("scene_style"), str) or not mockup_style["scene_style"].strip():
        raise ValueError("mockup_style")

    return payload


def validate_page_blueprint_artifact(payload: dict) -> dict:
    required_fields = {"run_id", "pages"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing page blueprint fields: {sorted(missing)}")

    pages = payload["pages"]
    if not isinstance(pages, list) or not pages:
        raise ValueError("pages")

    expected_page_number = 1
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("pages")
        if page.get("page_number") != expected_page_number:
            raise ValueError("page_number")
        if not isinstance(page.get("page_type"), str) or not page["page_type"].strip():
            raise ValueError("page_type")
        if not isinstance(page.get("title"), str) or not page["title"].strip():
            raise ValueError("title")
        if not isinstance(page.get("section_name"), str) or not page["section_name"].strip():
            raise ValueError("section_name")
        body = page.get("body")
        if not isinstance(body, list) or not body or any(not isinstance(item, str) or not item.strip() for item in body):
            raise ValueError("body")
        expected_page_number += 1

    return payload


def validate_render_manifest(payload: dict) -> dict:
    required_fields = {"run_id", "product_files", "page_count", "page_size", "preview_images", "design_template"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing render manifest fields: {sorted(missing)}")

    if not isinstance(payload["product_files"], list) or not payload["product_files"]:
        raise ValueError("product_files")

    if not isinstance(payload["preview_images"], list) or not payload["preview_images"]:
        raise ValueError("preview_images")

    if not isinstance(payload["page_count"], int) or payload["page_count"] <= 0:
        raise ValueError("page_count")

    if not isinstance(payload["design_template"], str) or not payload["design_template"].strip():
        raise ValueError("design_template")

    for path in payload["product_files"]:
        if not isinstance(path, str) or not path.startswith("product/") or not path.endswith(".pdf"):
            raise ValueError("product_files")

    for path in payload["preview_images"]:
        if not isinstance(path, str) or not path.startswith("product/") or not path.endswith(".png"):
            raise ValueError("preview_images")

    return payload


def validate_mockup_manifest(payload: dict) -> dict:
    required_fields = {"run_id", "mockup_files", "cover_image", "dimensions"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing mockup manifest fields: {sorted(missing)}")

    mockup_files = payload["mockup_files"]
    if not isinstance(mockup_files, list) or len(mockup_files) != 5:
        raise ValueError("mockup_files")

    for path in mockup_files:
        if not isinstance(path, str) or not path.startswith("mockups/") or not path.endswith(".png"):
            raise ValueError("mockup_files")

    cover_image = _require_relative_path(payload, "cover_image", ".png")
    if cover_image not in mockup_files:
        raise ValueError("cover_image")

    dimensions = payload["dimensions"]
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions")
    if not isinstance(dimensions.get("width"), int) or dimensions["width"] <= 0:
        raise ValueError("dimensions")
    if not isinstance(dimensions.get("height"), int) or dimensions["height"] <= 0:
        raise ValueError("dimensions")

    return payload


def validate_listing_manifest(payload: dict) -> dict:
    required_fields = {"run_id", "title_file", "description_file", "tags_file", "checklist_file"}
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"Missing listing manifest fields: {sorted(missing)}")

    title_file = _require_relative_path(payload, "title_file", ".txt")
    description_file = _require_relative_path(payload, "description_file", ".txt")
    tags_file = _require_relative_path(payload, "tags_file", ".txt")
    checklist_file = _require_relative_path(payload, "checklist_file", ".md")

    if title_file != "listing/titles.txt":
        raise ValueError("title_file")
    if description_file != "listing/description.txt":
        raise ValueError("description_file")
    if tags_file != "listing/tags.txt":
        raise ValueError("tags_file")
    if checklist_file != "listing/checklist.md":
        raise ValueError("checklist_file")

    return payload