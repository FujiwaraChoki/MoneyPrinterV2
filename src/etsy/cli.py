import os

from config import ROOT_DIR
from etsy.design_system import DesignSystemAgent
from etsy.listing_package import ListingPackageAgent
from etsy.mockups import MockupAgent
from etsy.io import discover_runs
from etsy.page_blueprint import PageBlueprintAgent
from etsy.pipeline import EtsyPipeline
from etsy.product_spec import ProductSpecAgent
from etsy.render_weasyprint import WeasyPrintRenderer
from etsy.research import ResearchAgent
from llm_provider import generate_text
from status import info
from status import question
from status import success
from status import warning


class _UnimplementedStage:
    def run(self, _run_dir: str) -> None:
        raise NotImplementedError("Etsy stage not implemented yet")


def build_etsy_pipeline() -> EtsyPipeline:
    return EtsyPipeline(
        ResearchAgent(generate_text),
        ProductSpecAgent(generate_text),
        DesignSystemAgent(generate_text),
        PageBlueprintAgent(generate_text),
        WeasyPrintRenderer(),
        MockupAgent(),
        ListingPackageAgent(),
    )


def start_etsy_cli() -> None:
    info("Starting Etsy Digital Products...")

    user_input = question("Select an option: 1. New run 2. Resume run 3. Quit ").strip()
    pipeline = build_etsy_pipeline()

    if user_input == "1":
        slug = question("Enter a slug for the new Etsy run: ").strip()
        output_root = os.path.join(ROOT_DIR, ".mp", "etsy")
        run_dir = pipeline.start_new_run(output_root, slug)
        success(f"Etsy run completed: {run_dir}")
        return

    if user_input == "2":
        runs = discover_runs(os.path.join(ROOT_DIR, ".mp", "etsy"))
        if not runs:
            warning("No Etsy runs found.")
            return

        selection = question("Select a run to resume: ").strip()
        selected_run = runs[int(selection) - 1]
        confirmation = question(
            f"Resume Etsy run '{selected_run['run_id']}' from the next incomplete stage? (yes/no): "
        ).strip().lower()
        if confirmation == "yes":
            pipeline.resume(selected_run["run_dir"])
            success(f"Etsy run completed: {selected_run['run_dir']}")
        return