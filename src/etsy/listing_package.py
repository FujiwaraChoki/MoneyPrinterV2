import json
import os
import re

from etsy.contracts import validate_listing_manifest
from etsy.contracts import validate_mockup_manifest
from etsy.contracts import validate_product_spec_artifact
from etsy.contracts import validate_render_manifest
from etsy.contracts import validate_research_artifact
from etsy.io import read_json
from etsy.io import write_json


class ListingPackageAgent:
    def __init__(self, text_generator=None):
        self.text_generator = text_generator

    def run(self, run_dir: str) -> str:
        research = read_json(os.path.join(run_dir, "artifacts", "research.json"))
        product_spec = read_json(os.path.join(run_dir, "artifacts", "product_spec.json"))
        render_manifest = read_json(os.path.join(run_dir, "artifacts", "render_manifest.json"))
        mockup_manifest = read_json(os.path.join(run_dir, "artifacts", "mockup_manifest.json"))

        validate_research_artifact(research)
        validate_product_spec_artifact(product_spec)
        validate_render_manifest(render_manifest)
        validate_mockup_manifest(mockup_manifest)

        listing_dir = os.path.join(run_dir, "listing")
        os.makedirs(listing_dir, exist_ok=True)

        title_path = os.path.join(listing_dir, "titles.txt")
        description_path = os.path.join(listing_dir, "description.txt")
        tags_path = os.path.join(listing_dir, "tags.txt")
        checklist_path = os.path.join(listing_dir, "checklist.md")

        with open(title_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(self._build_titles(product_spec)))
            handle.write("\n")

        with open(description_path, "w", encoding="utf-8") as handle:
            handle.write(self._build_description(research, product_spec, render_manifest))
            handle.write("\n")

        with open(tags_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(self._build_tags(research, product_spec)))
            handle.write("\n")

        with open(checklist_path, "w", encoding="utf-8") as handle:
            handle.write(self._build_checklist(product_spec, mockup_manifest))
            handle.write("\n")

        for path in (title_path, description_path, tags_path, checklist_path):
            with open(path, "r", encoding="utf-8") as handle:
                if not handle.read().strip():
                    raise ValueError(f"Listing file is empty: {os.path.basename(path)}")

        manifest = {
            "run_id": os.path.basename(run_dir),
            "title_file": "listing/titles.txt",
            "description_file": "listing/description.txt",
            "tags_file": "listing/tags.txt",
            "checklist_file": "listing/checklist.md",
        }
        validate_listing_manifest(manifest)

        manifest_path = os.path.join(run_dir, "artifacts", "listing_manifest.json")
        write_json(manifest_path, manifest)
        return manifest_path

    def _build_titles(self, product_spec: dict) -> list[str]:
        title_theme = product_spec["title_theme"]
        audience = product_spec["audience"]
        page_size = product_spec["page_size"]
        page_count = product_spec["page_count"]
        return [
            f"{title_theme} Printable PDF for {audience}",
            f"{title_theme} {page_count}-Page {page_size} Digital Download",
            f"{title_theme} Minimal {product_spec['product_type'].title()} for Focused Planning",
        ]

    def _build_description(self, research: dict, product_spec: dict, render_manifest: dict) -> str:
        section_names = [section["name"] for section in product_spec["sections"][:3]]
        section_name_text = ", ".join(section_names)
        top_benefits = [section["purpose"] for section in product_spec["sections"][:3]]

        return "\n".join(
            [
                f"{product_spec['title_theme']} is a printable {product_spec['product_type']} created for {product_spec['audience']}.",
                "",
                "WHAT'S INCLUDED",
                f"- {render_manifest['page_count']}-page {render_manifest['page_size']} PDF download",
                f"- Core pages such as {section_name_text}",
                f"- Instant download files: {len(render_manifest['product_files'])} PDF variations",
                "",
                "WHY YOU'LL LOVE IT",
                *[f"- {benefit}" for benefit in top_benefits],
                "",
                "HOW TO USE",
                "- Download instantly after purchase",
                "- Print at home, a local print shop, or use with a tablet note-taking workflow",
                "- Add the pages to a binder, clipboard, or digital planning routine",
                "",
                f"Built around the {research['selected_opportunity'].replace('-', ' ')} niche for shoppers looking for practical, focused planning tools.",
            ]
        )

    def _build_tags(self, research: dict, product_spec: dict) -> list[str]:
        if self.text_generator is not None:
            return self._generate_tags_llm(research, product_spec)
        return self._build_tags_static(research, product_spec)

    def _generate_tags_llm(self, research: dict, product_spec: dict) -> list[str]:
        prompt = (
            "You are an Etsy SEO specialist. Generate exactly 13 Etsy search tags for this listing.\n\n"
            f"Niche: {research['selected_opportunity'].replace('-', ' ')}\n"
            f"Product type: {product_spec['product_type']}\n"
            f"Target buyer: {product_spec['audience']}\n"
            f"Title theme: {product_spec['title_theme']}\n"
            f"Page size: {product_spec['page_size'].lower()}\n\n"
            "Rules:\n"
            "- Each tag max 20 characters (Etsy limit)\n"
            "- Include: 'printable planner', 'digital download', 'instant download', 'pdf planner'\n"
            "- Mix broad (high volume) and specific (low competition) tags\n"
            "- Use buyer-intent phrases buyers actually type\n"
            "- NO brand names, NO trademarked terms\n"
            "Return strict JSON: {\"tags\": [\"tag1\", \"tag2\", ...]}"
        )
        try:
            raw = self.text_generator(prompt)
            if not isinstance(raw, str):
                data = dict(raw)
            else:
                raw = raw.strip()
                fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
                data = json.loads(fenced.group(1) if fenced else raw)
            tags = data.get("tags", [])
            if isinstance(tags, list) and tags:
                return [str(t)[:20] for t in tags[:13]]
        except Exception:
            pass
        return self._build_tags_static(research, product_spec)

    def _build_tags_static(self, research: dict, product_spec: dict) -> list[str]:
        base_tags = [
            research["selected_opportunity"].replace("-", " "),
            product_spec["product_type"],
            "printable planner",
            "digital download",
            product_spec["page_size"].lower(),
            product_spec["audience"],
            product_spec["title_theme"].lower(),
            "minimal organizer",
            "instant download",
            "etsy printable",
            "home office",
            "budget tools",
            "pdf planner",
        ]
        return [tag[:20] for tag in base_tags]

    def _build_checklist(self, product_spec: dict, mockup_manifest: dict) -> str:
        return "\n".join(
            [
                "# Seller Checklist",
                f"- Confirm {product_spec['page_count']} pages exported correctly.",
                f"- Review all {len(mockup_manifest['mockup_files'])} listing images.",
                "- Proofread title candidates and description copy.",
                "- Verify tags match the target buyer and niche.",
                "- Upload the PDF and cover image before publishing on Etsy.",
            ]
        )