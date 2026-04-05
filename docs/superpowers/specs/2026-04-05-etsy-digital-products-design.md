# Etsy Digital Products Design

## Problem

`MoneyPrinterV2` currently focuses on social and outreach automations such as YouTube Shorts, Twitter posting, affiliate workflows, and outreach. It does not yet support a seller workflow for researching Etsy digital-product opportunities, generating a finished product, creating listing mockups, and assembling a seller-ready listing package.

The requested Etsy workflow is broader than a single prompt chain. It needs distinct responsibilities for:

- researching viable planner / tracker / worksheet opportunities
- turning the chosen opportunity into a concrete product brief
- rendering the actual downloadable files
- creating listing mockups and images
- assembling the listing copy and seller checklist

If those concerns are collapsed into one long runtime flow, the system will be difficult to inspect, retry, and extend later toward Etsy upload automation.

## Approved Direction

- Build the first Etsy workflow inside the existing CLI app rather than as a separate project
- Use a stage-based pipeline for the Etsy flow instead of a single monolithic run
- Optimize the first MVP for planner, tracker, and worksheet PDFs
- Produce a seller-ready output package containing product files, listing copy, tags, mockups, and a checklist
- Stop the first MVP before Etsy upload or publish automation

## Goals

1. Add a new Etsy-focused workflow that fits the current repo and CLI operating model
2. Generate a complete seller-ready package for a digital planner / tracker / worksheet listing
3. Keep research, rendering, mockup generation, and listing assembly separated into clear stages
4. Make pipeline runs resumable and inspectable through saved artifacts
5. Create a design that can later support an Etsy uploader without forcing that scope into the MVP

## Non-goals

- Automating Etsy browser upload or publish in the first MVP
- Supporting every digital-product category on day one
- Building a distributed worker system or queue infrastructure up front
- Refactoring unrelated YouTube, Twitter, affiliate, or outreach code

## Design

### 1. Architecture

The Etsy MVP should be added as a new provider workflow inside the current application, not as a separate app. The current CLI entry behavior in `src/main.py` should remain the top-level user entrypoint, but the Etsy flow should delegate into focused Etsy pipeline modules instead of growing `main.py` into another large inline branch.

CLI entry for the MVP:

- add a new top-level Etsy option to the existing numbered CLI menu in `src/main.py`
- insert Etsy before the existing quit / exit option so the final menu item remains exit
- selecting that option should start an Etsy-specific mini-flow with at least two actions: `new run` and `resume run`
- `new run` creates a fresh timestamped run directory and executes from `research`
- `resume run` lets the user pick an existing failed or incomplete run directory, shows the stage it will resume from, and asks for confirmation before restarting from the first incomplete stage

The Etsy workflow should be implemented as a stage-based pipeline with explicit boundaries:

1. `research`
2. `product_spec`
3. `render`
4. `mockups`
5. `listing_package`

Each stage should consume a structured input artifact and produce a structured output artifact. That artifact boundary is the main control surface for retries, resume support, inspection, and future uploader integration.

### 2. Components and agent boundaries

The MVP should be split into small units with one responsibility each.

Repo layout for the first implementation:

- add a focused Etsy package under `src/etsy/`
- keep `src/main.py` responsible only for CLI entry and dispatch into the Etsy pipeline
- intentionally do not force this workflow into a single `src/classes/Etsy.py` file, because the Etsy MVP has more stage boundaries and artifact contracts than the existing social-provider flows
- treat `src/etsy/` as a justified exception for this multi-stage workflow rather than as a repo-wide migration of all providers

Suggested responsibilities:

- `EtsyPipeline`: coordinates stages, run state, and overall execution
- `ResearchAgent`: produces ranked planner / tracker / worksheet opportunities
- `ProductSpecAgent`: converts the selected opportunity into a normalized product brief
- `PdfRenderer`: turns the brief into one or more downloadable PDF files
- `MockupAgent`: creates listing images from the rendered product assets
- `ListingPackageAgent`: writes seller-facing listing assets such as title, description, tags, and checklist

Implementation shape for the MVP:

- implement each stage as a focused class in `src/etsy/`
- `EtsyPipeline` owns orchestration and composes one instance of each stage class
- no shared abstract base class is required for the first version
- common helper code can live in small support modules such as `src/etsy/utils.py`, `src/etsy/io.py`, or similarly narrow helper modules when duplication appears

These units should not call each other directly in ad hoc ways. The coordinator owns sequencing, and each stage communicates through saved artifacts. That keeps the "agent" abstraction lightweight and testable while still allowing different prompt strategies or providers behind each stage.

### 3. Data flow and artifacts

Each Etsy run should create a timestamped run directory under `ROOT_DIR/.mp/etsy/`. The run directory should be named with a sortable timestamp plus a short slug, for example `20260405-143000-budget-planner`. The run directory should contain at least separate areas for:

- `artifacts/`
- `product/`
- `mockups/`
- `listing/`

Expected artifact flow:

1. `research` writes a ranked opportunity artifact with rationale and selected candidate
2. `product_spec` writes a normalized product brief artifact describing audience, page structure, copy tone, style rules, and output targets
3. `render` writes the generated PDF files plus a render manifest with dimensions, page count, and filenames
4. `mockups` reads the render manifest and writes listing images plus a mockup manifest
5. `listing_package` reads prior manifests and writes title, description, tags, and a seller checklist

Directory ownership for those outputs:

- `artifacts/` stores stage JSON manifests and normalized intermediate outputs such as the research result, selected concept, product brief, render manifest, mockup manifest, and listing manifest
- `product/` stores seller-deliverable downloadable files such as the rendered PDFs
- `mockups/` stores generated listing images intended for Etsy gallery use
- `listing/` stores human-readable listing assets such as title candidates, description copy, tag lists, and the seller checklist

Concrete file placement for the MVP should follow this pattern:

- `artifacts/run_status.json`
- `artifacts/research.json`
- `artifacts/product_spec.json`
- `artifacts/render_manifest.json`
- `artifacts/mockup_manifest.json`
- `artifacts/listing_manifest.json`
- `product/*.pdf`
- `mockups/*`
- `listing/titles.txt`
- `listing/description.txt`
- `listing/tags.txt`
- `listing/checklist.md`

Structured artifact contracts for the MVP should use JSON objects with these minimum fields:

- `artifacts/run_status.json`
	- `run_id`
	- `status` with one of `in_progress`, `failed`, or `completed`
	- `current_stage`
	- `last_successful_stage`
	- `failure_message` which may be empty when there is no failure
- `artifacts/research.json`
	- `run_id`
	- `category` with one of `planner`, `tracker`, or `worksheet`
	- `opportunities` as a list of ranked idea objects with at least `idea_slug`, `title`, `target_buyer`, `problem_solved`, and `score`
	- `selected_opportunity` as the chosen `idea_slug`
- `artifacts/product_spec.json`
	- `run_id`
	- `product_type`
	- `audience`
	- `title_theme`
	- `page_count`
	- `page_size`
	- `sections` as a list of objects with at least `name`, `purpose`, and `page_span`, where `page_span` is a positive integer count of pages allocated to that section
	- `style_notes` with at least `font_family`, `accent_color`, `spacing_density`, and `decor_style`
	- `output_files` as a list of expected run-directory-relative product paths such as `product/budget-planner.pdf`
- `artifacts/render_manifest.json`
	- `run_id`
	- `product_files` as a list of run-directory-relative file paths
	- `page_count`
	- `page_size`
	- `preview_images` as a list of run-directory-relative file paths
- `artifacts/mockup_manifest.json`
	- `run_id`
	- `mockup_files` as a list of run-directory-relative file paths
	- `cover_image` as a single run-directory-relative file path that must also appear in `mockup_files`
	- `dimensions` as an object with `width` and `height`
- `artifacts/listing_manifest.json`
	- `run_id`
	- `title_file`
	- `description_file`
	- `tags_file`
	- `checklist_file`

This structure gives the MVP three important properties:

- a run can resume from the last successful stage
- stage output is inspectable without reading code internals
- weak stages can be rerun without regenerating everything

Resume semantics for the MVP:

- resume always reuses artifacts from the same run directory
- resume is append-only within that run; it does not rewrite earlier successful stages unless the user starts a new run
- the pipeline determines the resume point by checking stage success markers in order and restarting from the first incomplete or failed stage
- if the user wants changed research inputs or a different chosen concept, that is a new run rather than a resume

Run discovery for the MVP:

- resume discovery scans `ROOT_DIR/.mp/etsy/` directly for timestamped run directories
- the CLI lists discovered runs in reverse chronological order
- each row should show the run directory name, current status, last successful stage, and any short failure message from `artifacts/run_status.json`
- the user resumes by selecting one of those discovered runs from the CLI table

Success-marker definition for the MVP:

- a stage counts as successful only when its required output artifact exists, parses successfully, and passes that stage's validation rules
- no separate `.success` files are required in the first version
- artifact existence alone is not enough to mark a stage successful

Run-state persistence for the MVP:

- `artifacts/run_status.json` is created at run start with `status=in_progress`
- after each successful stage, update `current_stage` and `last_successful_stage`
- when any stage fails validation or execution, update `status=failed` and write a short `failure_message`
- when all stages complete successfully, update `status=completed` and clear any failure message

It also creates a stable future handoff point for a later Etsy uploader, which can consume the final listing artifact rather than recreate business logic.

### 4. Product scope for the first MVP

The first implementation should target planner, tracker, and worksheet PDFs only.

Rationale:

- the layout constraints are tighter and easier to validate than highly open-ended art products
- PDF output is a practical default deliverable for Etsy digital planners and worksheets
- mockup generation is more repeatable when pages and aspect ratios are constrained
- listing copy and tags can be tuned around a narrower category before broadening the system

The first MVP should support category selection within that family through research, but it should not attempt to support unrelated product categories such as Canva template packs or printable wall art in the same spec.

### 5. Output package contract

The first MVP should produce a seller-ready package, not just the raw downloadable file.

The expected package should include:

- final downloadable product files
- listing title candidates
- listing description copy
- tag candidates
- generated mockups / listing images
- a checklist summarizing what a human seller should review before publishing

Mockup contract for the MVP:

- generate exactly `5` listing images per run
- output PNG files for the first version to avoid format ambiguity
- use a square or Etsy-friendly portrait composition chosen consistently by the mockup stage for all images in the run
- include at least one cover-style image, two interior-page previews, one bundle or multi-page composition, and one dimension-or-features image

Mockup generation mapping for the MVP:

- convert rendered PDF pages into preview images first, then build mockups from those previews
- the cover-style image uses the strongest first-page or title-page preview with simple background framing
- the two interior previews use two distinct page previews when available; if the PDF has only one page, reuse that page with two different crops or presentations
- the bundle or multi-page composition uses a simple stacked or side-by-side layout of multiple page previews on one canvas
- the dimension-or-features image combines one preview with short text callouts such as page count, page size, or included sections
- PDFs with fewer distinct pages than mockup slots should still produce the full set of listing images by varying composition rather than failing

Title-candidate storage for the MVP:

- store multiple title candidates in `listing/titles.txt`
- write one candidate per line
- store the path to `listing/titles.txt` in `listing_manifest.json` as `title_file`

The MVP should stop there. It should not yet produce an Etsy-upload automation contract, browser upload flow, or publish step.

### 6. Error handling

Each stage should validate its output before handing off to the next stage.

Minimum validation expectations:

- `research` must output at least one structured opportunity, and `selected_opportunity` must match one of the ranked opportunities
- `product_spec` must output a complete brief with all required fields: `product_type`, `audience`, `title_theme`, `page_count`, `page_size`, `sections`, `style_notes`, and `output_files`
- `product_spec.page_count` must be a positive integer
- `product_spec.sections` must be a non-empty list
- `product_spec.style_notes.accent_color` must use a hex color string such as `#4F7CAC`
- `render` must confirm all expected product files listed in `output_files` exist and that `render_manifest.page_count` matches `product_spec.page_count`
- `mockups` must confirm exactly five expected listing images exist and that every path in `mockup_manifest.mockup_files` exists under the run directory
- `listing_package` must confirm `titles.txt`, `description.txt`, `tags.txt`, and `checklist.md` were written and are non-empty

If a stage fails validation, the pipeline should:

- stop immediately
- mark the run as failed
- preserve all prior artifacts for inspection
- avoid silent retries or hidden recovery behavior in the MVP

This fail-fast behavior is preferable for the first version because it makes weak prompts, missing files, and provider failures visible rather than masking them.

### 7. Testing

Testing should focus on stage contracts and deterministic boundaries rather than LLM prose quality.

Add or update tests for:

1. stage input/output artifact validation
2. run-directory and manifest creation
3. pipeline resumability from the last successful stage
4. failure reporting when a stage produces invalid or missing output
5. one smoke-style Etsy pipeline test with external generation mocked or stubbed

Prompt-heavy code should remain behind thin adapters so tests can verify schema, files, and control flow instead of brittle text snapshots.

## Implementation notes

- Preserve the current CLI-first user experience
- Prefer adding focused Etsy modules rather than expanding `src/main.py` with large new inline logic
- Keep stage outputs explicit and serializable so they can be reused by later upload automation
- Defer Etsy browser automation until after the seller-ready package pipeline is stable
- use `reportlab` for first-version PDF rendering so page composition stays deterministic and local
- add `reportlab>=4,<5` to `requirements.txt` when implementation begins
- use `Pillow` for first-version mockup composition and annotation
- use run-directory-relative paths in all manifests rather than absolute paths
- default PDF page sizes should be constrained to a small supported set such as US Letter and A4 in portrait orientation for the MVP
- PDF rendering failures should fail the `render` stage immediately and write the error into `run_status.json`

## Expected outcome

After this work, the repo should support an Etsy MVP workflow that:

- researches a planner / tracker / worksheet opportunity
- chooses and specifies a concrete digital product
- renders downloadable PDF assets
- creates listing mockups
- assembles seller-ready listing copy and tags
- writes all outputs into an inspectable run folder

Acceptance criteria:

1. the Etsy workflow runs as a new CLI-accessible path inside the repo
2. the workflow is split into explicit stages with artifact handoffs
3. the first MVP targets planner / tracker / worksheet PDFs only
4. the final output includes product files, listing copy, tags, mockups, and a seller checklist
5. failed stages stop the run and preserve prior artifacts for inspection
6. the design leaves a clean future path to Etsy upload automation without including it in the MVP