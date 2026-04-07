import os

from etsy.io import create_run_directory
from etsy.io import initialize_run_status
from etsy.io import read_json
from etsy.io import update_run_status


STAGE_SEQUENCE = ["research", "product_spec", "design_system", "page_blueprint", "render", "mockups", "listing_package"]


class EtsyPipeline:
    def __init__(self, research_agent, product_spec_agent, design_system_agent, page_blueprint_agent, renderer, mockup_agent, listing_agent):
        self.research_agent = research_agent
        self.product_spec_agent = product_spec_agent
        self.design_system_agent = design_system_agent
        self.page_blueprint_agent = page_blueprint_agent
        self.renderer = renderer
        self.mockup_agent = mockup_agent
        self.listing_agent = listing_agent

    def start_new_run(self, output_root: str, slug: str) -> str:
        os.makedirs(output_root, exist_ok=True)
        run_dir = create_run_directory(output_root, slug)
        initialize_run_status(run_dir)

        for stage_name in STAGE_SEQUENCE:
            self.run_stage(stage_name, run_dir)

        return run_dir

    def resume(self, run_dir: str) -> None:
        status_payload = read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        last_successful_stage = status_payload.get("last_successful_stage", "")

        if last_successful_stage in STAGE_SEQUENCE:
            start_index = STAGE_SEQUENCE.index(last_successful_stage) + 1
        else:
            start_index = 0

        for stage_name in STAGE_SEQUENCE[start_index:]:
            self.run_stage(stage_name, run_dir)

    def run_stage(self, stage_name: str, run_dir: str) -> None:
        agent_map = {
            "research": self.research_agent,
            "product_spec": self.product_spec_agent,
            "design_system": self.design_system_agent,
            "page_blueprint": self.page_blueprint_agent,
            "render": self.renderer,
            "mockups": self.mockup_agent,
            "listing_package": self.listing_agent,
        }
        previous_status = read_json(os.path.join(run_dir, "artifacts", "run_status.json"))

        try:
            agent_map[stage_name].run(run_dir)
        except Exception as exc:
            update_run_status(
                run_dir,
                status="failed",
                current_stage=stage_name,
                last_successful_stage=previous_status.get("last_successful_stage", ""),
                failure_message=str(exc),
            )
            raise

        new_status = {
            "status": "completed" if stage_name == "listing_package" else "in_progress",
            "current_stage": stage_name,
            "last_successful_stage": stage_name,
            "failure_message": "",
        }
        update_run_status(run_dir, **new_status)