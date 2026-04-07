import json
import os
import re

from etsy.contracts import VALID_TEMPLATE_FAMILIES
from etsy.contracts import validate_design_system_artifact
from etsy.io import read_json
from etsy.io import write_json


class DesignSystemAgent:
    def __init__(self, text_generator):
        self.text_generator = text_generator

    def run(self, run_dir: str) -> str:
        product_spec = read_json(os.path.join(run_dir, "artifacts", "product_spec.json"))
        raw_payload = self.text_generator(self._build_prompt(product_spec))
        payload = self._coerce_payload(raw_payload)
        payload = self._normalize_payload(payload, product_spec)

        payload["run_id"] = os.path.basename(run_dir)
        validate_design_system_artifact(payload)

        artifact_path = os.path.join(run_dir, "artifacts", "design_system.json")
        write_json(artifact_path, payload)
        return artifact_path

    def _build_prompt(self, product_spec: dict) -> str:
        families = ", ".join(sorted(VALID_TEMPLATE_FAMILIES))
        return (
            "Generate a normalized Etsy printable design system as strict JSON. "
            f"Product type: {product_spec.get('product_type', '')}. "
            f"Title theme: {product_spec.get('title_theme', '')}. "
            f"Audience: {product_spec.get('audience', '')}. "
            "Return palette, typography, layout, and mockup_style fields only. "
            "palette must include primary, secondary, and background hex colors. "
            "typography must include heading_font and body_font. "
            f"layout must include template_name, header_style, page_frame_style, and template_family. "
            f"template_family must be one of: {families}. "
            "Choose template_family based on the product aesthetic: "
            "clean-minimal for budget/finance/habit, dark-luxury for executive/focus planners, "
            "cottagecore for wedding/pregnancy/garden, bold-playful for ADHD/teacher/fitness. "
            "mockup_style must include background_color and scene_style."
        )

    def _coerce_payload(self, raw_payload):
        if not isinstance(raw_payload, str):
            return dict(raw_payload)

        raw_text = raw_payload.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fenced_match:
            raw_text = fenced_match.group(1)
        return json.loads(raw_text)

    def _normalize_payload(self, payload: dict, product_spec: dict) -> dict:
        normalized = dict(payload)
        normalized["palette"] = self._normalize_palette(normalized.get("palette", {}))
        normalized["typography"] = self._normalize_typography(normalized.get("typography", {}))
        normalized["layout"] = self._normalize_layout(normalized, product_spec)
        normalized["mockup_style"] = self._normalize_mockup_style(normalized)
        return normalized

    def _normalize_palette(self, palette) -> dict:
        if not isinstance(palette, dict):
            palette = {}

        swatches = palette.get("swatches") if isinstance(palette.get("swatches"), dict) else {}
        primary = self._pick_hex(
            palette.get("primary"),
            swatches.get("primary_structural"),
            swatches.get("accent_focus"),
            default="#4F7CAC",
        )
        secondary = self._pick_hex(
            palette.get("secondary"),
            swatches.get("secondary_soft"),
            swatches.get("accent_focus"),
            default="#D9C6A5",
        )
        background = self._pick_hex(
            palette.get("background"),
            swatches.get("background_base"),
            default="#FFF9F1",
        )

        return {
            "primary": primary,
            "secondary": secondary,
            "background": background,
        }

    def _normalize_typography(self, typography) -> dict:
        if not isinstance(typography, dict):
            typography = {}

        font_families = typography.get("font_families") if isinstance(typography.get("font_families"), dict) else {}
        headings = font_families.get("headings") if isinstance(font_families.get("headings"), dict) else {}
        body_text = font_families.get("body_text") if isinstance(font_families.get("body_text"), dict) else {}

        heading_font = str(
            typography.get("heading_font")
            or headings.get("font_name")
            or "Helvetica-Bold"
        ).strip() or "Helvetica-Bold"
        body_font = str(
            typography.get("body_font")
            or body_text.get("font_name")
            or "Helvetica"
        ).strip() or "Helvetica"

        return {
            "heading_font": heading_font,
            "body_font": body_font,
        }

    def _normalize_layout(self, payload: dict, product_spec: dict) -> dict:
        layout = payload.get("layout") if isinstance(payload.get("layout"), dict) else {}
        template_name = str(
            layout.get("template_name")
            or payload.get("design_system_name")
            or "etsy-printable"
        ).strip()
        header_style = str(layout.get("header_style") or layout.get("description") or "clean-header").strip()

        page_frame_style = str(layout.get("page_frame_style") or "").strip()
        if not page_frame_style:
            components = layout.get("components") if isinstance(layout.get("components"), dict) else {}
            component_text = " ".join(str(value) for value in components.values())
            page_frame_style = "soft-rounded" if "rounded" in component_text.lower() else "clean-frame"

        raw_family = str(layout.get("template_family") or "").strip().lower()
        template_family = (
            raw_family
            if raw_family in VALID_TEMPLATE_FAMILIES
            else self._infer_template_family(payload, product_spec)
        )

        return {
            "template_name": self._slugify(template_name),
            "header_style": self._slugify(header_style),
            "page_frame_style": self._slugify(page_frame_style),
            "template_family": template_family,
        }

    def _infer_template_family(self, payload: dict, product_spec: dict) -> str:
        style_notes = product_spec.get("style_notes") if isinstance(product_spec.get("style_notes"), dict) else {}
        layout = payload.get("layout") if isinstance(payload.get("layout"), dict) else {}
        mockup_style = payload.get("mockup_style") if isinstance(payload.get("mockup_style"), dict) else {}
        sections = product_spec.get("sections") if isinstance(product_spec.get("sections"), list) else []

        context_parts = [
            product_spec.get("product_type", ""),
            product_spec.get("audience", ""),
            product_spec.get("title_theme", ""),
            style_notes.get("font_family", ""),
            style_notes.get("decor_style", ""),
            layout.get("template_name", ""),
            layout.get("header_style", ""),
            layout.get("page_frame_style", ""),
            mockup_style.get("scene_style", ""),
            mockup_style.get("aesthetic", ""),
        ]
        for section in sections:
            if not isinstance(section, dict):
                continue
            context_parts.append(section.get("name", ""))
            context_parts.append(section.get("purpose", ""))

        context = " ".join(str(part or "") for part in context_parts).lower()

        if any(
            keyword in context
            for keyword in (
                "wedding",
                "bridal",
                "bride",
                "pregnancy",
                "baby",
                "nursery",
                "garden",
                "botanical",
                "floral",
                "boho",
                "bohemian",
                "rustic",
                "homestead",
                "gratitude",
                "ritual",
                "self-care",
                "mindful",
                "eucalyptus",
                "earthy",
            )
        ):
            return "cottagecore"

        if any(
            keyword in context
            for keyword in (
                "adhd",
                "teacher",
                "classroom",
                "fitness",
                "workout",
                "kids",
                "student",
                "study",
                "social media",
                "content batching",
                "playful",
                "dopamine",
                "neurodivergent",
            )
        ):
            return "bold-playful"

        if any(
            keyword in context
            for keyword in (
                "executive",
                "luxury",
                "premium",
                "founder",
                "ceo",
                "focus",
                "stoic",
                "reading",
                "night",
                "black",
                "minimal noir",
            )
        ):
            return "dark-luxury"

        return "clean-minimal"

    def _normalize_mockup_style(self, payload: dict) -> dict:
        mockup_style = payload.get("mockup_style") if isinstance(payload.get("mockup_style"), dict) else {}
        environment = mockup_style.get("environment") if isinstance(mockup_style.get("environment"), dict) else {}

        background_color = self._pick_hex(
            mockup_style.get("background_color"),
            payload.get("palette", {}).get("background") if isinstance(payload.get("palette"), dict) else None,
            default="#F4EFE7",
        )
        scene_style = str(
            mockup_style.get("scene_style")
            or mockup_style.get("aesthetic")
            or environment.get("setting")
            or "desk-flatlay"
        ).strip()

        return {
            "background_color": background_color,
            "scene_style": self._slugify(scene_style),
        }

    def _pick_hex(self, *values, default: str) -> str:
        for value in values:
            text = str(value or "").strip()
            if re.match(r"^#[0-9A-Fa-f]{6}$", text):
                return text.upper()
        return default

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
        return slug or "default"