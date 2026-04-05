# YouTube Cinematic Motion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automatic cinematic motion to generated YouTube Shorts image clips without introducing crossfades or changing subtitle and audio timing.

**Architecture:** Extend config parsing with motion settings, factor image clip preparation out of `combine()`, and add a deterministic cinematic motion helper that applies linear zoom plus optional horizontal pan using the existing MoviePy pipeline. Keep cuts hard and the rest of the render flow unchanged.

**Tech Stack:** Python 3.12, MoviePy, `unittest`, JSON config

---

## File map

- Modify: `src/config.py` — add motion-setting getters with safe defaults.
- Modify: `tests/test_config.py` — add config coverage for the new motion settings.
- Create: `tests/test_youtube_cinematic_motion.py` — add helper-level motion tests.
- Modify: `src/classes/YouTube.py` — factor clip preparation into helpers and add deterministic cinematic motion.
- Modify: `config.example.json` — document the new config keys.
- Modify: `config.json` — enable cinematic motion for the active local config.
- Modify: `docs/Configuration.md` — document the new motion keys and defaults.
- Reference: `docs/superpowers/specs/2026-04-04-youtube-cinematic-motion-design.md` — approved design spec for motion behavior and acceptance criteria.

## Chunk 1: Config and helper contracts

### Task 1: Add failing tests for motion config getters

**Files:**
- Modify: `tests/test_config.py`

- [ ] **Step 1: Add tests for the motion settings**

- [ ] **Step 0: Verify the approved spec is present**

Run:

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
test -f docs/superpowers/specs/2026-04-04-youtube-cinematic-motion-design.md
```

Expected: exit code `0`.

Add tests covering:
- `get_video_motion_style()` defaults to `static`
- `get_video_motion_style()` normalizes `cinematic`
- invalid style falls back to `static`
- `get_video_zoom_intensity()` defaults to `1.08`
- invalid or too-small zoom falls back to `1.08`
- `get_video_pan_enabled()` defaults to `True`
- `get_video_pan_intensity()` defaults to `0.03`
- invalid or non-positive pan intensity falls back to `0.03`

- [ ] **Step 2: Run the focused config tests and verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_config -v`

Expected: FAIL with missing getter functions.

### Task 2: Add failing tests for cinematic motion helper behavior

**Files:**
- Create: `tests/test_youtube_cinematic_motion.py`

- [ ] **Step 1: Add helper-level tests**

Add tests covering:
- static mode returns the prepared clip directly
- cinematic mode wraps the clip in a `CompositeVideoClip`
- cinematic mode uses a linear zoom function
- even and odd indices produce opposite horizontal drift directions using the clip index from the `combine()` image iteration order as the source of truth
- pan disabled keeps horizontal drift centered
- motion-enabled clips do not change duration or break the surrounding composition contract needed for subtitles and audio timing

- [ ] **Step 2: Run the focused helper tests and verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_youtube_cinematic_motion -v`

Expected: FAIL because the helper methods do not exist yet.

## Chunk 2: Minimal implementation

### Task 3: Implement motion config getters

**Files:**
- Modify: `src/config.py`
- Modify: `config.example.json`
- Modify: `config.json`
- Modify: `docs/Configuration.md`

- [ ] **Step 1: Add config getters in `src/config.py`**

Implement:
- `get_video_motion_style()`
- `get_video_zoom_intensity()`
- `get_video_pan_enabled()`
- `get_video_pan_intensity()`

Use these defaults:
- style: `static`
- zoom: `1.08`
- pan enabled: `true`
- pan intensity: `0.03`

- [ ] **Step 2: Add the keys to `config.example.json`**

Add:

```json
"video_motion_style": "static",
"video_zoom_intensity": 1.08,
"video_pan_enabled": true,
"video_pan_intensity": 0.03,
```

- [ ] **Step 3: Enable the feature in the active `config.json`**

Add:

```json
"video_motion_style": "cinematic",
"video_zoom_intensity": 1.08,
"video_pan_enabled": true,
"video_pan_intensity": 0.03,
```

- [ ] **Step 4: Update `docs/Configuration.md`**

Document each new key, fallback behavior, and the difference between `static` and `cinematic`.

- [ ] **Step 5: Re-run the config tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_config -v`

Expected: PASS.

### Task 4: Add deterministic motion helpers and wire them into `combine()`

**Files:**
- Modify: `src/classes/YouTube.py`
- Create: `tests/test_youtube_cinematic_motion.py`

- [ ] **Step 1: Factor base clip preparation into a helper**

Create a helper such as `_build_base_image_clip(image_path, duration)` that keeps the existing crop/resize/fps logic intact.

- [ ] **Step 2: Add the cinematic motion helper**

Create these helpers:
- `_build_motion_clip(image_path: str, duration: float, index: int)`
- `_build_motion_positioner(duration: float, index: int, pan_enabled: bool, pan_intensity: float, zoom_intensity: float)`

Behavior:
- static mode returns the base clip unchanged
- cinematic mode applies linear zoom from `1.0` to configured zoom
- cinematic mode applies deterministic horizontal drift based on the clip index passed from the `combine()` image iteration order
- hard cuts remain unchanged

- [ ] **Step 3: Update `combine()` to use the helper**

Replace inline `ImageClip` setup with the new helper, but keep duration allocation, concatenation, subtitles, and audio mixing behavior unchanged.

- [ ] **Step 4: Run the focused motion helper tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_youtube_cinematic_motion -v`

Expected: PASS.

## Chunk 3: Final verification

### Task 5: Run the relevant regression slice

**Files:**
- No additional file changes

- [ ] **Step 1: Run the broader regression suite**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_config tests.test_youtube_cinematic_motion tests.test_youtube_prompt_generation tests.test_youtube_upload_diagnostics tests.test_youtube_image_provider tests.test_main_runtime -v`

Expected: PASS.

- [ ] **Step 1a: Confirm motion clips preserve duration**

Ensure the motion helper tests assert that motion-enabled clips keep the requested duration so audio and subtitle timing are not shifted by the motion wrapper.

- [ ] **Step 2: Validate JSON config files**

Run:

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
./venv/bin/python -m json.tool config.json >/dev/null
./venv/bin/python -m json.tool config.example.json >/dev/null
```

Expected: both commands exit successfully.

- [ ] **Step 3: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add src/config.py src/classes/YouTube.py tests/test_config.py tests/test_youtube_cinematic_motion.py config.json config.example.json docs/Configuration.md docs/superpowers/specs/2026-04-04-youtube-cinematic-motion-design.md docs/superpowers/plans/2026-04-05-youtube-cinematic-motion.md
git commit -m "feat: add cinematic motion to youtube shorts"
```