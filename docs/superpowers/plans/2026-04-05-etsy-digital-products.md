# Etsy Digital Products Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Etsy MVP workflow that researches a planner, tracker, or worksheet idea, generates a seller-ready digital-product package, and supports resumable stage-based runs inside the existing MoneyPrinterV2 CLI.

**Architecture:** Keep the existing CLI entry in `src/main.py`, but dispatch Etsy behavior into a dedicated `src/etsy/` package. Model the workflow as five explicit stages with artifact contracts saved under `.mp/etsy/<run>/`, and implement stage validation plus resume behavior around those artifacts rather than hidden in prompts.

**Tech Stack:** Python 3.12, `unittest`, `reportlab`, `Pillow`, JSON artifacts, PrettyTable, existing OpenRouter-backed text generation utilities

---

## File map

- Modify: `requirements.txt` — add `reportlab>=4,<5` for deterministic PDF generation.
- Modify: `src/constants.py` — insert an Etsy option before the existing quit option.
- Modify: `src/main.py` — dispatch the Etsy menu entry into the new Etsy CLI helper.
- Create: `src/etsy/__init__.py` — Etsy package marker and shared exports if needed.
- Create: `src/etsy/cli.py` — Etsy mini-menu, run discovery, resume confirmation, and top-level dispatch.
- Create: `src/etsy/io.py` — run-directory creation, run discovery, JSON read/write helpers, and run-status persistence.
- Create: `src/etsy/contracts.py` — stage names, artifact validation helpers, and run-state helpers.
- Create: `src/etsy/pipeline.py` — `EtsyPipeline` orchestration, stage sequencing, and resume logic.
- Create: `src/etsy/research.py` — `ResearchAgent` that produces `research.json`.
- Create: `src/etsy/product_spec.py` — `ProductSpecAgent` that produces `product_spec.json`.
- Create: `src/etsy/render.py` — `PdfRenderer` using `reportlab` and preview image generation for rendered pages.
- Create: `src/etsy/mockups.py` — `MockupAgent` using `Pillow` to produce exactly five listing PNGs.
- Create: `src/etsy/listing_package.py` — `ListingPackageAgent` that writes titles, description, tags, checklist, and `listing_manifest.json`.
- Create: `tests/test_etsy_io.py` — run-directory, discovery, and run-status persistence coverage.
- Create: `tests/test_etsy_contracts.py` — artifact schema and validation coverage.
- Create: `tests/test_etsy_cli.py` — Etsy mini-menu and resume-confirmation coverage.
- Create: `tests/test_etsy_pipeline.py` — stage orchestration, resume behavior, and failure handling coverage.
- Create: `tests/test_etsy_render.py` — deterministic PDF render manifest coverage.
- Create: `tests/test_etsy_mockups.py` — exact five-image output coverage and fallback composition coverage.
- Modify: `tests/test_main_runtime.py` — new main-menu dispatch coverage for Etsy entry.
- Modify: `README.md` — add short usage guidance for the Etsy workflow after the implementation is working.

## Chunk 1: CLI entry, dependency, and artifact scaffolding

### Task 1: Add the Etsy menu entry and CLI dispatch

**Files:**
- Modify: `src/constants.py`
- Modify: `src/main.py`
- Create: `src/etsy/__init__.py`
- Create: `src/etsy/cli.py`
- Modify: `tests/test_main_runtime.py`

- [ ] **Step 1: Write the failing main-menu test**

```python
def test_main_dispatches_to_etsy_cli_when_etsy_option_selected(self) -> None:
    with patch.object(self.main, "bootstrap_runtime"), \
         patch.object(self.main, "input", side_effect=["5"]), \
         patch("etsy.cli.start_etsy_cli") as start_etsy_cli_mock:
        self.main.main()

    start_etsy_cli_mock.assert_called_once_with()
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_main_runtime.MainRuntimeTests.test_main_dispatches_to_etsy_cli_when_etsy_option_selected -v`
Expected: FAIL because the Etsy option and dispatch path do not exist yet.

- [ ] **Step 3: Insert the Etsy option before Quit**

Update `src/constants.py` so `OPTIONS` becomes:

```python
OPTIONS = [
    "YouTube Shorts Automation",
    "Twitter Bot",
    "Affiliate Marketing",
    "Outreach",
    "Etsy Digital Products",
    "Quit",
]
```

- [ ] **Step 4: Add minimal Etsy CLI entrypoint module**

Create `src/etsy/cli.py` with a temporary callable surface:

```python
def start_etsy_cli() -> None:
    info("Starting Etsy Digital Products...")
```

Create `src/etsy/__init__.py` so the package imports cleanly.

- [ ] **Step 5: Wire `src/main.py` to dispatch to the Etsy CLI**

Add an explicit `elif user_input == 5:` branch that imports and calls `start_etsy_cli()`, and shift the existing quit branch to `elif user_input == 6:` so the other numbered flows stay unchanged.

- [ ] **Step 6: Re-run the targeted test**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_main_runtime.MainRuntimeTests.test_main_dispatches_to_etsy_cli_when_etsy_option_selected -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/constants.py src/main.py src/etsy/__init__.py src/etsy/cli.py tests/test_main_runtime.py
git commit -m "feat: add etsy cli entrypoint"
```

### Task 2: Add dependency and run-storage helpers

**Files:**
- Modify: `requirements.txt`
- Create: `src/etsy/io.py`
- Create: `tests/test_etsy_io.py`

- [ ] **Step 1: Write the failing run-storage tests**

```python
class EtsyIoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    def test_create_run_directory_creates_expected_subfolders(self) -> None:
        run_dir = etsy_io.create_run_directory(self.temp_dir, "budget-planner")
        self.assertRegex(os.path.basename(run_dir), r"^\d{8}-\d{6}-budget-planner$")
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "artifacts")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "product")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "mockups")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "listing")))

    def test_initialize_run_status_writes_in_progress_payload(self) -> None:
        run_dir = etsy_io.create_run_directory(self.temp_dir, "budget-planner")
        status_path = etsy_io.initialize_run_status(run_dir)
        with open(status_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["last_successful_stage"], "")

    def test_write_json_and_read_json_round_trip(self) -> None:
        target_path = os.path.join(self.temp_dir, "example.json")
        etsy_io.write_json(target_path, {"hello": "world"})
        self.assertEqual(etsy_io.read_json(target_path), {"hello": "world"})
```

- [ ] **Step 2: Run the new IO tests to verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_io -v`
Expected: FAIL because `src/etsy/io.py` does not exist yet.

- [ ] **Step 3: Add `reportlab` to dependencies**

Update `requirements.txt` by adding:

```text
reportlab>=4,<5
```

- [ ] **Step 4: Implement minimal run-directory and run-status helpers**

Create `src/etsy/io.py` with:

```python
RUN_SUBDIRECTORIES = ("artifacts", "product", "mockups", "listing")

def create_run_directory(base_dir: str, slug: str) -> str:
    ...

def initialize_run_status(run_dir: str) -> str:
    ...

def write_json(path: str, payload: dict) -> None:
    ...

def read_json(path: str) -> dict:
    ...
```

Keep the implementation minimal: create the timestamped run directory, make the four subdirectories, and write `artifacts/run_status.json` with the initial schema from the spec. The caller should pass the Etsy output root itself, for example `os.path.join(ROOT_DIR, ".mp", "etsy")`, and `create_run_directory()` should append a directory name in `YYYYMMDD-HHMMSS-<slug>` format.

- [ ] **Step 5: Re-run the IO tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_io -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add requirements.txt src/etsy/io.py tests/test_etsy_io.py
git commit -m "feat: add etsy run storage helpers"
```

### Task 3: Define artifact contracts and validation helpers

**Files:**
- Create: `src/etsy/contracts.py`
- Create: `tests/test_etsy_contracts.py`

- [ ] **Step 1: Write failing validation tests for research and product spec artifacts**

```python
class EtsyContractsTests(unittest.TestCase):
    def test_validate_research_artifact_rejects_empty_opportunities(self) -> None:
        with self.assertRaisesRegex(ValueError, "opportunities"):
            contracts.validate_research_artifact({
                "run_id": "run-1",
                "category": "planner",
                "opportunities": [],
                "selected_opportunity": "budget-planner",
            })

    def test_validate_research_artifact_requires_selected_slug_membership(self) -> None:
        with self.assertRaisesRegex(ValueError, "selected_opportunity"):
            contracts.validate_research_artifact({
                "run_id": "run-1",
                "category": "planner",
                "opportunities": [{
                    "idea_slug": "meal-planner",
                    "title": "Meal Planner",
                    "target_buyer": "parents",
                    "problem_solved": "weekly meal planning",
                    "score": 0.9,
                }],
                "selected_opportunity": "budget-planner",
            })

    def test_validate_product_spec_rejects_non_hex_accent_color(self) -> None:
        with self.assertRaisesRegex(ValueError, "accent_color"):
            contracts.validate_product_spec_artifact({
                "run_id": "run-1",
                "product_type": "planner",
                "audience": "students",
                "title_theme": "Budget",
                "page_count": 3,
                "page_size": "LETTER",
                "sections": [{"name": "Weekly", "purpose": "tracking", "page_span": 3}],
                "style_notes": {
                    "font_family": "Helvetica",
                    "accent_color": "blue",
                    "spacing_density": "medium",
                    "decor_style": "minimal",
                },
                "output_files": ["product/budget-planner.pdf"],
            })

    def test_validate_product_spec_requires_non_empty_sections_and_positive_page_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_count"):
            contracts.validate_product_spec_artifact({
                "run_id": "run-1",
                "product_type": "planner",
                "audience": "students",
                "title_theme": "Budget",
                "page_count": 0,
                "page_size": "LETTER",
                "sections": [],
                "style_notes": {
                    "font_family": "Helvetica",
                    "accent_color": "#4F7CAC",
                    "spacing_density": "medium",
                    "decor_style": "minimal",
                },
                "output_files": ["product/budget-planner.pdf"],
            })

    def test_validate_run_status_rejects_unknown_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "status"):
            contracts.validate_run_status({
                "run_id": "run-1",
                "status": "broken",
                "current_stage": "research",
                "last_successful_stage": "",
                "failure_message": "",
            })
```

- [ ] **Step 2: Run the contract tests to verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_contracts -v`
Expected: FAIL because the validation helpers do not exist yet.

- [ ] **Step 3: Implement contract constants and validation helpers**

Create `src/etsy/contracts.py` with:

```python
STAGE_NAMES = ("research", "product_spec", "render", "mockups", "listing_package")

def validate_research_artifact(payload: dict) -> dict:
    ...

def validate_product_spec_artifact(payload: dict) -> dict:
    ...

def validate_run_status(payload: dict) -> dict:
    ...
```

Only implement the validations needed for Chunk 1: required fields, non-empty opportunities, selected slug membership, positive `page_count`, non-empty `sections`, hex-color validation, and valid run-status values.

- [ ] **Step 4: Re-run the contract tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_contracts -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/contracts.py tests/test_etsy_contracts.py
git commit -m "feat: add etsy artifact contracts"
```

## Chunk 2: Pipeline orchestration, research, and product spec stages

### Task 4: Implement pipeline resume and stage sequencing

**Files:**
- Modify: `src/etsy/cli.py`
- Modify: `src/etsy/io.py`
- Create: `src/etsy/pipeline.py`
- Create: `tests/test_etsy_cli.py`
- Create: `tests/test_etsy_pipeline.py`

- [ ] **Step 1: Write failing pipeline and CLI tests for new-run and resume behavior**

```python
class EtsyPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()

    def make_existing_run(self, last_successful_stage: str, status: str) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.update_run_status(
            run_dir,
            status=status,
            current_stage=last_successful_stage,
            last_successful_stage=last_successful_stage,
            failure_message="boom" if status == "failed" else "",
        )
        return run_dir

    def make_run_dir(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        return run_dir

    def make_run_dir_with_research(self) -> str:
        run_dir = self.make_run_dir()
        etsy_io.write_json(os.path.join(run_dir, "artifacts", "research.json"), {
            "run_id": os.path.basename(run_dir),
            "category": "planner",
            "opportunities": [{
                "idea_slug": "budget-planner",
                "title": "Budget Planner",
                "target_buyer": "busy adults",
                "problem_solved": "monthly budgeting",
                "score": 0.92,
            }],
            "selected_opportunity": "budget-planner",
        })
        return run_dir

    def test_resume_uses_first_incomplete_stage(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock())
        run_dir = self.make_existing_run(last_successful_stage="research", status="failed")
        with patch.object(pipeline, "run_stage", return_value=None) as run_stage_mock:
            pipeline.resume(run_dir)
        run_stage_mock.assert_any_call("product_spec", run_dir)

    def test_new_run_executes_stages_in_order(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock())
        with patch.object(pipeline, "run_stage", return_value=None) as run_stage_mock:
            pipeline.start_new_run(self.base_dir, "budget-planner")
        self.assertEqual(
            [call.args[0] for call in run_stage_mock.call_args_list[:2]],
            ["research", "product_spec"],
        )

    def test_resume_discovery_lists_runs_in_reverse_chronological_order(self) -> None:
        runs = etsy_io.discover_runs(self.base_dir)
        self.assertEqual([run["run_id"] for run in runs], ["20260405-120000-b", "20260405-110000-a"])

    def test_resume_skips_malformed_run_directories(self) -> None:
        runs = etsy_io.discover_runs(self.base_dir)
        self.assertFalse(any(run["run_id"] == "malformed" for run in runs))

    def test_run_status_updates_after_successful_stage(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock())
        run_dir = self.make_run_dir()
        pipeline.run_stage("research", run_dir)
        status = etsy_io.read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        self.assertEqual(status["current_stage"], "research")
        self.assertEqual(status["last_successful_stage"], "research")

    def test_failed_stage_marks_run_failed_and_sets_failure_message(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock())
        run_dir = self.make_run_dir()
        with patch.object(pipeline.research_agent, "run", side_effect=ValueError("bad research artifact")):
            with self.assertRaisesRegex(ValueError, "bad research artifact"):
                pipeline.run_stage("research", run_dir)

        status = etsy_io.read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        self.assertEqual(status["status"], "failed")
        self.assertIn("bad research artifact", status["failure_message"])

class EtsyCliTests(unittest.TestCase):
    def test_cli_resume_requires_confirmation_before_pipeline_resume(self) -> None:
           # side_effect order: select "resume run" -> choose first run -> decline confirmation
           with patch("etsy.cli.discover_runs", return_value=[{"run_id": "run-1", "run_dir": "/tmp/run-1", "status": "failed", "last_successful_stage": "research", "failure_message": "boom"}]), \
               patch("etsy.cli.question", side_effect=["2", "1", "no"]), \
               patch("etsy.cli.build_etsy_pipeline") as build_pipeline_mock:
            start_etsy_cli()

           build_pipeline_mock.return_value.resume.assert_not_called()

    def test_cli_new_run_dispatches_to_pipeline(self) -> None:
           # side_effect order: select "new run" -> provide slug
           with patch("etsy.cli.question", side_effect=["1", "budget-planner"]), \
               patch("etsy.cli.build_etsy_pipeline") as build_pipeline_mock:
            start_etsy_cli()

           build_pipeline_mock.return_value.start_new_run.assert_called_once()
```

- [ ] **Step 2: Run the pipeline tests to verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline -v`
Expected: FAIL because discovery and pipeline logic do not exist yet.

- [ ] **Step 3: Implement run discovery and resume helpers**

Add to `src/etsy/io.py`:

```python
def discover_runs(base_dir: str) -> list[dict]:
    ...

def update_run_status(run_dir: str, **changes: str) -> dict:
    ...
```

Implement reverse-chronological directory scanning under `.mp/etsy`, loading `artifacts/run_status.json`, and gracefully skipping malformed directories.
Use the validation helpers from `src/etsy/contracts.py` when determining whether a stage is complete; artifact existence by itself is never enough.
Return dictionaries with keys `run_id`, `run_dir`, `status`, `current_stage`, `last_successful_stage`, and `failure_message`.

- [ ] **Step 4: Implement minimal `EtsyPipeline` sequencing**

Create `src/etsy/pipeline.py` with:

```python
class EtsyPipeline:
    def __init__(self, research_agent, product_spec_agent, renderer, mockup_agent, listing_agent):
        ...

    def start_new_run(self, output_root: str, slug: str) -> str:
        ...

    def resume(self, run_dir: str) -> None:
        ...

    def run_stage(self, stage_name: str, run_dir: str) -> None:
        ...
```

Only wire the stage order and run-status transitions in this task; the stage implementations themselves can still be stubs.
When resuming, set `current_stage` to the stage being retried and preserve `last_successful_stage` until the retried stage passes.

- [ ] **Step 5: Finish `src/etsy/cli.py` by wiring the existing Etsy mini-menu to the pipeline**

Implement:
- a small Etsy menu using numeric choices
- run discovery table display for resume
- confirmation prompt before resuming from the computed stage
- dispatch into `EtsyPipeline`
- test coverage for `new run`, `resume run`, and decline-to-resume behavior

In Task 4, add a `build_etsy_pipeline()` helper in `src/etsy/cli.py` and patch that helper in CLI tests. Keep `build_etsy_pipeline()` as the single construction point for `EtsyPipeline`. In Tasks 5 through 9, replace its temporary placeholder stage objects with the real `ResearchAgent`, `ProductSpecAgent`, `PdfRenderer`, `MockupAgent`, and `ListingPackageAgent` instances as those classes are implemented.
Import and use the existing `question()` helper from `src/utils.py` inside `src/etsy/cli.py`; patch `etsy.cli.question` in CLI tests because that is where the helper is used.

- [ ] **Step 6: Re-run the pipeline and CLI tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline tests.test_etsy_cli -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/cli.py src/etsy/io.py src/etsy/pipeline.py tests/test_etsy_pipeline.py
git add tests/test_etsy_cli.py
git commit -m "feat: add etsy pipeline orchestration"
```

### Task 5: Implement research stage with deterministic tests

**Files:**
- Create: `src/etsy/research.py`
- Modify: `src/etsy/pipeline.py`
- Modify: `tests/test_etsy_pipeline.py`

- [ ] **Step 1: Write a failing test for research artifact creation**

```python
def test_research_stage_writes_valid_research_artifact(self) -> None:
    agent = ResearchAgent(text_generator=lambda prompt: {
        "category": "planner",
        "opportunities": [{
            "idea_slug": "budget-planner",
            "title": "Budget Planner",
            "target_buyer": "busy adults",
            "problem_solved": "monthly budgeting",
            "score": 0.92,
        }],
        "selected_opportunity": "budget-planner",
    })
    run_dir = self.make_run_dir()
    artifact_path = agent.run(run_dir)
    payload = etsy_io.read_json(artifact_path)
    self.assertEqual(payload["category"], "planner")
    self.assertTrue(payload["opportunities"])
    self.assertIn(payload["selected_opportunity"], [item["idea_slug"] for item in payload["opportunities"]])
```

- [ ] **Step 2: Run the targeted research test to verify it fails**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline.EtsyPipelineTests.test_research_stage_writes_valid_research_artifact -v`
Expected: FAIL because `ResearchAgent` does not exist yet.

- [ ] **Step 3: Implement minimal `ResearchAgent`**

Create `src/etsy/research.py` with a `run(run_dir: str) -> str` method that:
- writes `artifacts/research.json`
- emits one deterministic ranked opportunity in tests
- validates the payload through `contracts.validate_research_artifact()` before saving

Use dependency injection for text generation so tests can stub it. The callable contract is: one prompt string in, one dict or JSON string out. The agent should call the injected callable once, normalize JSON-string responses into dicts, validate the result, and write it as the artifact. In tests, return the deterministic fixture shown in Step 1 rather than opaque raw prose.
The agent should call the existing contract validator from Chunk 1 rather than re-implementing schema checks.

- [ ] **Step 4: Wire the research stage into `EtsyPipeline.run_stage()`**

Call `research_agent.run(run_dir)` for the `research` stage and update `run_status.json` after success.

- [ ] **Step 5: Re-run the targeted research test**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline.EtsyPipelineTests.test_research_stage_writes_valid_research_artifact -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/research.py src/etsy/pipeline.py tests/test_etsy_pipeline.py
git commit -m "feat: add etsy research stage"
```

### Task 6: Implement product-spec stage

**Files:**
- Create: `src/etsy/product_spec.py`
- Modify: `src/etsy/pipeline.py`
- Modify: `tests/test_etsy_pipeline.py`

- [ ] **Step 1: Write a failing test for product-spec artifact creation**

```python
def test_product_spec_stage_writes_valid_product_spec(self) -> None:
    run_dir = self.make_run_dir_with_research()
    agent = ProductSpecAgent(text_generator=lambda prompt: {
        "product_type": "planner",
        "audience": "busy adults",
        "title_theme": "Budget Planner",
        "page_count": 3,
        "page_size": "LETTER",
        "sections": [{"name": "Monthly Overview", "purpose": "budget planning", "page_span": 3}],
        "style_notes": {
            "font_family": "Helvetica",
            "accent_color": "#4F7CAC",
            "spacing_density": "medium",
            "decor_style": "minimal",
        },
        "output_files": ["product/budget-planner.pdf"],
    })
    artifact_path = agent.run(run_dir)
    payload = etsy_io.read_json(artifact_path)
    self.assertEqual(payload["product_type"], "planner")
    self.assertTrue(payload["audience"])
    self.assertGreater(payload["page_count"], 0)
    self.assertTrue(payload["sections"])
    self.assertEqual(set(payload["sections"][0].keys()), {"name", "purpose", "page_span"})
    self.assertEqual(payload["output_files"], ["product/budget-planner.pdf"])
    self.assertEqual(payload["title_theme"], "Budget Planner")
    self.assertEqual(payload["style_notes"]["accent_color"], "#4F7CAC")
```

- [ ] **Step 2: Run the targeted product-spec test to verify it fails**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline.EtsyPipelineTests.test_product_spec_stage_writes_valid_product_spec -v`
Expected: FAIL because `ProductSpecAgent` does not exist yet.

- [ ] **Step 3: Implement `ProductSpecAgent`**

Create `src/etsy/product_spec.py` with a `run(run_dir: str) -> str` method that:
- reads `artifacts/research.json`
- converts the selected opportunity into a normalized product brief
- writes `artifacts/product_spec.json`
- validates through `contracts.validate_product_spec_artifact()` before saving

For the test fixture created by `make_run_dir_with_research()`, use a selected opportunity slug of `budget-planner` so the deterministic output path is exactly `product/budget-planner.pdf` and the product spec clearly reflects the chosen research input.

Use injected text-generation helpers instead of calling `generate_text()` directly inside tests. The product-spec prompt should request JSON with exactly the artifact-contract keys, and invalid JSON should raise `ValueError` immediately rather than being repaired silently.

- [ ] **Step 4: Wire the product-spec stage into the pipeline**

Update `EtsyPipeline.run_stage()` to call the new stage after research and update `run_status.json` appropriately.

- [ ] **Step 5: Re-run the targeted product-spec test**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline.EtsyPipelineTests.test_product_spec_stage_writes_valid_product_spec -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/product_spec.py src/etsy/pipeline.py tests/test_etsy_pipeline.py
git commit -m "feat: add etsy product spec stage"
```

## Chunk 3: Rendering, mockups, listing package, and documentation

### Task 7: Implement deterministic PDF rendering and render manifest output

**Files:**
- Create: `src/etsy/render.py`
- Modify: `src/etsy/contracts.py`
- Modify: `src/etsy/pipeline.py`
- Create: `tests/test_etsy_render.py`

- [ ] **Step 1: Write the failing render test**

```python
class EtsyRenderTests(unittest.TestCase):
    def make_run_dir_with_product_spec(self) -> str:
        ...

    def make_run_dir_with_invalid_product_spec(self) -> str:
        ...

    def test_renderer_writes_pdf_and_render_manifest(self) -> None:
        renderer = PdfRenderer()
        run_dir = self.make_run_dir_with_product_spec()
        manifest_path = renderer.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)
        self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
        self.assertTrue(os.path.exists(os.path.join(run_dir, "product", "budget-planner.pdf")))
        self.assertEqual(manifest["product_files"], ["product/budget-planner.pdf"])
        self.assertEqual(manifest["page_count"], 3)
        self.assertEqual(manifest["page_size"], "LETTER")
        self.assertTrue(manifest["preview_images"])
        for relative_path in manifest["preview_images"]:
            self.assertTrue(os.path.exists(os.path.join(run_dir, relative_path)))

    def test_renderer_validation_failure_marks_run_failed(self) -> None:
        renderer = PdfRenderer()
        run_dir = self.make_run_dir_with_invalid_product_spec()
        with self.assertRaises(ValueError):
            renderer.run(run_dir)
```

- [ ] **Step 2: Run the render test to verify it fails**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_render -v`
Expected: FAIL because the renderer does not exist yet.

- [ ] **Step 3: Implement minimal `PdfRenderer` with `reportlab`**

Create `src/etsy/render.py` with a `run(run_dir: str) -> str` method that:
- reads `artifacts/product_spec.json`
- writes the expected PDF file to `product/`
- writes `artifacts/render_manifest.json`
- produces at least one preview image path entry in the manifest for the mockup stage to consume

Keep the first version deterministic: use one simple page template, supported page sizes `LETTER` and `A4`, and direct `reportlab` drawing primitives.
`PdfRenderer` must create the actual preview image files on disk and include their run-relative paths in `render_manifest.json`; the mockup stage should only consume those files, not generate the previews itself.
Use a single deterministic layout template: a title block at the top, a thin accent divider, and repeated section boxes derived from `product_spec.sections` so page structure is stable across test runs.
Extend `src/etsy/contracts.py` with `validate_render_manifest(payload: dict) -> dict` and call it before saving the manifest.
That validator should enforce required fields `run_id`, `product_files`, `page_count`, `page_size`, and `preview_images`, plus on-disk existence of every listed file.
Generate preview images as PNG files using `Pillow` from the same normalized layout data used to build the PDF, with fixed size `1200x1200` for the MVP.

- [ ] **Step 4: Wire the render stage into the pipeline**

Update `EtsyPipeline.run_stage()` and the stage ordering so render runs after product spec.

- [ ] **Step 5: Re-run the render test**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_render -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/render.py src/etsy/pipeline.py tests/test_etsy_render.py
git commit -m "feat: add etsy pdf renderer"
```

### Task 8: Implement exact-five mockup generation

**Files:**
- Create: `src/etsy/mockups.py`
- Modify: `src/etsy/contracts.py`
- Modify: `src/etsy/pipeline.py`
- Create: `tests/test_etsy_mockups.py`

- [ ] **Step 1: Write the failing mockup tests**

```python
class EtsyMockupTests(unittest.TestCase):
    def make_run_dir_with_render_manifest(self) -> str:
        ...

    def make_single_page_run_dir(self) -> str:
        ...

    def make_run_dir_with_missing_preview_file(self) -> str:
        ...

    def test_mockup_agent_writes_exactly_five_pngs(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_run_dir_with_render_manifest()
        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)
        self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
        self.assertEqual(len(manifest["mockup_files"]), 5)
        self.assertIn(manifest["cover_image"], manifest["mockup_files"])
        self.assertEqual(set(manifest["dimensions"].keys()), {"width", "height"})
        for relative_path in manifest["mockup_files"]:
            self.assertTrue(relative_path.endswith(".png"))
            self.assertTrue(os.path.exists(os.path.join(run_dir, relative_path)))

    def test_mockup_agent_reuses_single_page_preview_with_different_presentations(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_single_page_run_dir()
        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)
        self.assertEqual(len(manifest["mockup_files"]), 5)

    def test_mockup_validation_failure_marks_run_failed(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_run_dir_with_missing_preview_file()
        with self.assertRaises(ValueError):
            agent.run(run_dir)
```

- [ ] **Step 2: Run the mockup tests to verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_mockups -v`
Expected: FAIL because the mockup agent does not exist yet.

- [ ] **Step 3: Implement `MockupAgent` with `Pillow`**

Create `src/etsy/mockups.py` with a `run(run_dir: str) -> str` method that:
- reads `artifacts/render_manifest.json`
- creates exactly five PNG listing images under `mockups/`
- writes `artifacts/mockup_manifest.json`

Use a deterministic set of compositions:
- one cover layout
- two preview layouts
- one multi-page bundle layout
- one features layout with text callouts

Use one fixed canvas size for the entire run, `2000x2000`, so all generated images share consistent square dimensions.

Extend `src/etsy/contracts.py` with `validate_mockup_manifest(payload: dict) -> dict` and call it before saving the manifest.
That validator should enforce required fields `run_id`, `mockup_files`, `cover_image`, and `dimensions`, ensure `cover_image` appears in `mockup_files`, and ensure every listed file exists.

- [ ] **Step 4: Wire the mockups stage into the pipeline**

Update the stage order and run-status updates so mockups run after render.

- [ ] **Step 5: Re-run the mockup tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_mockups -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/mockups.py src/etsy/pipeline.py tests/test_etsy_mockups.py
git commit -m "feat: add etsy mockup generation"
```

### Task 9: Implement listing-package output and end-to-end smoke coverage

**Files:**
- Create: `src/etsy/listing_package.py`
- Modify: `src/etsy/contracts.py`
- Modify: `src/etsy/pipeline.py`
- Modify: `tests/test_etsy_pipeline.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing listing-package test**

```python
def test_listing_package_stage_writes_titles_description_tags_and_checklist(self) -> None:
    run_dir = self.make_run_dir_with_mockups()
    agent = ListingPackageAgent(text_generator=lambda prompt: {
        "titles": ["Budget Planner", "Minimal Budget Planner", "Printable Budget Planner"],
        "description": "A clean printable planner for monthly budgeting.",
        "tags": ["budget planner", "printable planner", "finance tracker"],
        "checklist": "- Review PDF pages\n- Review mockups\n- Review pricing",
    })
    manifest_path = agent.run(run_dir)
    manifest = etsy_io.read_json(manifest_path)
    self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
    self.assertEqual(manifest["title_file"], "listing/titles.txt")
    self.assertEqual(manifest["description_file"], "listing/description.txt")
    self.assertEqual(manifest["tags_file"], "listing/tags.txt")
    self.assertEqual(manifest["checklist_file"], "listing/checklist.md")
    self.assertTrue(os.path.exists(os.path.join(run_dir, "listing", "titles.txt")))
    self.assertTrue(os.path.exists(os.path.join(run_dir, "listing", "description.txt")))
    self.assertTrue(os.path.exists(os.path.join(run_dir, "listing", "tags.txt")))
    self.assertTrue(os.path.exists(os.path.join(run_dir, "listing", "checklist.md")))

def test_listing_package_validation_failure_marks_run_failed(self) -> None:
    run_dir = self.make_run_dir_with_mockups()
    agent = ListingPackageAgent(text_generator=lambda prompt: {"titles": [], "description": "", "tags": [], "checklist": ""})
    with self.assertRaises(ValueError):
        agent.run(run_dir)
```

- [ ] **Step 2: Run the targeted listing-package test to verify it fails**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_pipeline.EtsyPipelineTests.test_listing_package_stage_writes_titles_description_tags_and_checklist -v`
Expected: FAIL because the listing-package agent does not exist yet.

- [ ] **Step 3: Implement `ListingPackageAgent`**

Create `src/etsy/listing_package.py` with a `run(run_dir: str) -> str` method that:
- reads `research.json`, `product_spec.json`, `render_manifest.json`, and `mockup_manifest.json`
- writes `listing/titles.txt`, `listing/description.txt`, `listing/tags.txt`, and `listing/checklist.md`
- writes `artifacts/listing_manifest.json`

Use dependency injection for text generation and keep the first version deterministic in tests. The injected callable should be invoked once and return a dict with `titles`, `description`, `tags`, and `checklist` keys.
Extend `src/etsy/contracts.py` with `validate_listing_manifest(payload: dict) -> dict` and call it before saving the manifest.
That validator should enforce required fields `run_id`, `title_file`, `description_file`, `tags_file`, and `checklist_file`, plus non-empty on-disk content for each referenced listing file.

- [ ] **Step 4: Wire the listing-package stage into the pipeline and full completion state**

Update the final pipeline stage to:
- mark `last_successful_stage` as `listing_package`
- set `status` to `completed`
- clear `failure_message`

Keep those status transitions in `EtsyPipeline`, not inside `ListingPackageAgent`.

- [ ] **Step 5: Add one smoke-style end-to-end pipeline test**

Extend `tests/test_etsy_pipeline.py` with one flow that stubs text generation and verifies a full run creates:
- all six artifact files
- at least one PDF
- exactly five mockups
- all listing text files
- `run_status.json` with `status == "completed"`

Use a concrete test named `test_full_etsy_pipeline_creates_completed_seller_ready_run`.

- [ ] **Step 6: Run the Etsy test suite**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_etsy_io tests.test_etsy_contracts tests.test_etsy_pipeline tests.test_etsy_render tests.test_etsy_mockups -v`
Expected: PASS.

- [ ] **Step 7: Add a short README usage section**

Document:
- where the Etsy option appears in the CLI
- where generated runs are stored
- that the MVP stops before Etsy upload

- [ ] **Step 8: Run the broader regression tests that touch the main runtime**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && source venv/bin/activate && python -m unittest tests.test_main_runtime tests.test_llm_provider tests.test_config tests.test_preflight_local -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/etsy/listing_package.py src/etsy/pipeline.py tests/test_etsy_pipeline.py README.md
git commit -m "feat: add etsy listing package workflow"
```