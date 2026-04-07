import json
import os
import re

from etsy.contracts import validate_page_blueprint_artifact
from etsy.io import read_json
from etsy.io import write_json


class PageBlueprintAgent:
    def __init__(self, text_generator):
        self.text_generator = text_generator

    def run(self, run_dir: str) -> str:
        product_spec = read_json(os.path.join(run_dir, "artifacts", "product_spec.json"))
        design_system = read_json(os.path.join(run_dir, "artifacts", "design_system.json"))

        raw_payload = self.text_generator(self._build_prompt(product_spec, design_system))
        payload = self._coerce_payload(raw_payload)
        payload = self._normalize_payload(payload, product_spec)
        payload["run_id"] = os.path.basename(run_dir)

        validate_page_blueprint_artifact(payload)

        artifact_path = os.path.join(run_dir, "artifacts", "page_blueprint.json")
        write_json(artifact_path, payload)
        return artifact_path

    def _build_prompt(self, product_spec: dict, design_system: dict) -> str:
        sections = product_spec.get("sections", [])
        section_names = ", ".join(s.get("name", "") for s in sections)

        few_shot = json.dumps(
            [
                {
                    "page_number": 1,
                    "page_type": "worksheet",
                    "section_name": "Daily Focus",
                    "title": "Set Your Daily Intentions",
                    "body": [
                        "What is the ONE thing you must accomplish today?",
                        "Name your biggest distraction and your plan to avoid it.",
                        "Schedule one deep-work block: ___:___ to ___:___",
                        "Rate your energy level (1-5) and adjust your plan accordingly.",
                        "Capture tomorrow's top priority before you close today.",
                    ],
                },
                {
                    "page_number": 2,
                    "page_type": "schedule",
                    "section_name": "Time Blocks",
                    "title": "Your Daily Time Map",
                    "body": [
                        "6:00 AM - Morning Routine",
                        "8:00 AM - Deep Work Block 1",
                        "12:00 PM - Lunch and Reset",
                        "2:00 PM - Deep Work Block 2",
                        "5:00 PM - Wind-Down Review",
                    ],
                },
                {
                    "page_number": 3,
                    "page_type": "tracker",
                    "section_name": "Habit Tracking",
                    "title": "Weekly Habit Tracker",
                    "body": [
                        "Morning pages or journaling",
                        "30-minute focused work session",
                        "Phone-free morning before 9 AM",
                        "End-of-day task review",
                        "15-minute walk or movement break",
                    ],
                },
                {
                    "page_number": 4,
                    "page_type": "reflection",
                    "section_name": "Weekly Review",
                    "title": "End-of-Week Reflection",
                    "body": [
                        "What did I accomplish this week that I am most proud of?",
                        "Where did I lose focus, and what will I do differently?",
                        "Rate this week's productivity (1-10) and explain your score.",
                        "Name one habit to strengthen next week.",
                        "What is the most important thing I can do for myself next week?",
                    ],
                },
            ],
            indent=2,
        )

        return (
            f"Generate a strict JSON page blueprint for an Etsy printable.\n"
            f"Title theme: {product_spec.get('title_theme', '')}.\n"
            f"Audience: {product_spec.get('audience', '')}.\n"
            f"Page count: {product_spec.get('page_count', 1)}.\n"
            f"Sections: {section_names}.\n"
            f"Design template: {design_system.get('layout', {}).get('template_name', '')}.\n\n"
            "Return JSON with a pages array. Each page must include page_number, page_type "
            "(one of: worksheet / schedule / tracker / reflection), section_name, title, and body.\n"
            "body must be a list of 4-5 specific, actionable, commercially useful lines -- prompts, "
            "time-slot labels, habit names, or guided reflection questions tailored to the title theme "
            "and audience above. Vary the page types across sections.\n\n"
            "Adapt the following example to the title theme and sections above:\n\n"
            f"{few_shot}"
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
        pages = payload.get("pages") if isinstance(payload, dict) else None
        normalized_pages = self._normalize_pages(pages, product_spec)
        return {"pages": normalized_pages}

    def _normalize_pages(self, pages, product_spec: dict) -> list[dict]:
        if not isinstance(pages, list) or not pages:
            return self._build_default_pages(product_spec)

        normalized_pages = []
        for index, page in enumerate(pages, start=1):
            if not isinstance(page, dict):
                continue
            body = page.get("body")
            if not isinstance(body, list) or not body:
                body = (
                    page.get("content")
                    or page.get("prompts")
                    or page.get("checklist")
                    or page.get("reflection_questions")
                    or page.get("prompt_blocks")
                    or []
                )
            normalized_body = [str(item).strip() for item in body if str(item).strip()][:5]
            if not normalized_body:
                normalized_body = self._default_body(page.get("section_name") or page.get("title") or "Planner")

            normalized_pages.append(
                {
                    "page_number": index,
                    "page_type": str(page.get("page_type") or page.get("page_kind") or page.get("layout") or "worksheet").strip() or "worksheet",
                    "section_name": str(page.get("section_name") or page.get("section") or page.get("headline") or page.get("title") or "Overview").strip() or "Overview",
                    "title": str(page.get("title") or page.get("headline") or page.get("section_name") or page.get("section") or f"Page {index}").strip() or f"Page {index}",
                    "body": normalized_body,
                }
            )

        target_count = int(product_spec.get("page_count") or len(normalized_pages) or 1)
        if len(normalized_pages) < target_count:
            defaults = self._build_default_pages(product_spec)
            for page in defaults[len(normalized_pages):target_count]:
                normalized_pages.append(page)

        return normalized_pages[:target_count]

    def _build_default_pages(self, product_spec: dict) -> list[dict]:
        page_count = max(1, int(product_spec.get("page_count") or 1))
        sections = product_spec.get("sections") or [{"name": "Overview", "purpose": "planning", "page_span": 1}]
        pages = []
        section_index = 0

        while len(pages) < page_count:
            section = sections[section_index % len(sections)]
            page_span = max(1, int(section.get("page_span") or 1))
            for span_index in range(page_span):
                if len(pages) >= page_count:
                    break
                section_name = str(section.get("name") or "Overview")
                title = section_name if page_span == 1 else f"{section_name} {span_index + 1}"
                pages.append(
                    {
                        "page_number": len(pages) + 1,
                        "page_type": self._infer_page_type(section_name, section.get("purpose", "")),
                        "section_name": section_name,
                        "title": title,
                        "body": self._default_body(section.get("purpose") or section_name),
                    }
                )
            section_index += 1

        return pages

    def _infer_page_type(self, section_name: str, purpose: str) -> str:
        text = f"{section_name} {purpose}".lower()
        if "track" in text or "habit" in text:
            return "tracker"
        if "reflect" in text or "journal" in text:
            return "reflection"
        if "schedule" in text or "time" in text:
            return "schedule"
        return "worksheet"

    def _default_body(self, seed_text: str) -> list[str]:
        cleaned = str(seed_text or "planning").strip().rstrip(".")
        return [
            f"Set your priority for {cleaned.lower()}.",
            "Capture key tasks, notes, or wins for this page.",
            "Review progress and choose the next actionable step.",
        ]