import json
import os
import re

from etsy.contracts import validate_product_spec_artifact
from etsy.io import read_json
from etsy.io import write_json


class ProductSpecAgent:
    def __init__(self, text_generator):
        self.text_generator = text_generator

    def run(self, run_dir: str) -> str:
        research_payload = read_json(os.path.join(run_dir, "artifacts", "research.json"))
        raw_payload = self.text_generator(self._build_prompt(research_payload))
        payload = self._coerce_payload(raw_payload)
        payload = self._normalize_payload(payload)

        payload["run_id"] = os.path.basename(run_dir)
        validate_product_spec_artifact(payload)

        artifact_path = os.path.join(run_dir, "artifacts", "product_spec.json")
        write_json(artifact_path, payload)
        return artifact_path

    def _build_prompt(self, research_payload: dict) -> str:
        return (
            "Generate a normalized Etsy product specification as strict JSON for the selected opportunity: "
            f"{research_payload.get('selected_opportunity', '')}. "
            "Include product_type, audience, title_theme, page_count, page_size, sections, style_notes, and output_files. "
            "product_type must be planner, tracker, or worksheet. "
            "page_size must be a single supported size string such as LETTER or A4. "
            "Each section must include name, purpose, and page_span. "
            "style_notes must include font_family, accent_color, spacing_density, and decor_style. "
            "output_files must be run-relative paths such as product/example.pdf."
        )

    def _coerce_payload(self, raw_payload):
        if not isinstance(raw_payload, str):
            return dict(raw_payload)

        raw_text = raw_payload.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fenced_match:
            raw_text = fenced_match.group(1)
        return json.loads(raw_text)

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)

        normalized["product_type"] = self._normalize_product_type(normalized.get("product_type"))
        normalized["audience"] = self._normalize_audience(normalized.get("audience"))
        normalized["page_size"] = self._normalize_page_size(normalized.get("page_size"))
        normalized["sections"] = self._normalize_sections(normalized.get("sections", []))
        normalized["style_notes"] = self._normalize_style_notes(normalized.get("style_notes", {}))
        normalized["output_files"] = self._normalize_output_files(normalized.get("output_files", []))

        return normalized

    def _normalize_product_type(self, value) -> str:
        text = str(value or "").lower()
        if "tracker" in text:
            return "tracker"
        if "worksheet" in text:
            return "worksheet"
        return "planner"

    def _normalize_audience(self, value) -> str:
        if isinstance(value, dict):
            for field_name in ("primary", "secondary"):
                field_value = str(value.get(field_name, "")).strip()
                if field_value:
                    return field_value
            return "general audience"
        text = str(value or "").strip()
        return text or "general audience"

    def _normalize_page_size(self, value) -> str:
        if isinstance(value, list):
            candidates = [str(item).strip().upper() for item in value if str(item).strip()]
        else:
            candidates = [str(value or "").strip().upper()]

        if any(candidate in {"LETTER", "US LETTER", "US_LETTER"} for candidate in candidates):
            return "LETTER"
        if "A4" in candidates:
            return "A4"

        for candidate in candidates:
            if candidate:
                return "LETTER"
        return "LETTER"

    def _normalize_sections(self, sections) -> list[dict]:
        normalized_sections = []
        if not isinstance(sections, list):
            return normalized_sections

        for section in sections:
            if not isinstance(section, dict):
                continue
            elements = section.get("elements")
            if isinstance(elements, list) and elements:
                purpose = ", ".join(str(item).strip() for item in elements[:2] if str(item).strip())
                page_span = max(1, len(elements))
            else:
                purpose = str(section.get("purpose") or section.get("description") or "planning").strip()
                raw_span = section.get("page_span")
                page_span = raw_span if isinstance(raw_span, int) and raw_span > 0 else 1

            normalized_sections.append(
                {
                    "name": str(section.get("name") or section.get("section_name") or "Section").strip(),
                    "purpose": purpose or "planning",
                    "page_span": page_span,
                }
            )

        return normalized_sections or [{"name": "Overview", "purpose": "planning", "page_span": 1}]

    def _normalize_style_notes(self, style_notes) -> dict:
        if not isinstance(style_notes, dict):
            style_notes = {}

        typography = str(style_notes.get("typography") or style_notes.get("font_family") or "Helvetica").strip()
        aesthetic = str(style_notes.get("aesthetic") or style_notes.get("decor_style") or "minimal").strip()
        color_text = str(style_notes.get("accent_color") or style_notes.get("color_palette") or "").lower()

        if re.match(r"^#[0-9a-f]{6}$", color_text, re.IGNORECASE):
            accent_color = color_text.upper()
        elif "earth" in color_text:
            accent_color = "#8C6A43"
        elif "pastel" in color_text:
            accent_color = "#A7B8C9"
        else:
            accent_color = "#4F7CAC"

        spacing_density = str(style_notes.get("spacing_density") or "medium").strip().lower() or "medium"

        return {
            "font_family": typography.split(",")[0] or "Helvetica",
            "accent_color": accent_color,
            "spacing_density": spacing_density,
            "decor_style": aesthetic.lower() or "minimal",
        }

    def _normalize_output_files(self, output_files) -> list[str]:
        if not isinstance(output_files, list) or not output_files:
            return ["product/printable.pdf"]

        normalized_files = []
        for output_file in output_files:
            filename = os.path.basename(str(output_file).strip())
            stem, extension = os.path.splitext(filename)
            safe_stem = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "printable"
            safe_extension = extension.lower() if extension.lower() == ".pdf" else ".pdf"
            normalized_files.append(f"product/{safe_stem}{safe_extension}")

        return normalized_files