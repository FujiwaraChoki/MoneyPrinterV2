# YouTube Cinematic Motion Design

## Problem

The current YouTube Shorts render pipeline uses static image clips with hard cuts.

In `src/classes/YouTube.py`, `combine()`:

- loads each generated image as an `ImageClip`
- crops and resizes it to vertical format
- assigns a fixed duration per image
- concatenates the clips directly

This works, but the resulting videos feel like slideshow cuts rather than cinematic short-form storytelling.

## Approved Direction

- Add automatic cinematic motion to image clips inside the existing MoviePy pipeline
- Do not add crossfades or overlapping transitions
- Keep subtitle generation, audio mixing, and overall clip timing behavior unchanged
- Make the feature configurable so it can be enabled or tuned without code edits

## Goals

1. Make still images feel alive with subtle motion
2. Improve atmosphere for mystery, disaster, and historical storytelling content
3. Keep the implementation low-risk and compatible with the current render flow
4. Avoid flashy transition effects that conflict with the desired cinematic tone

## Non-goals

- Crossfades or overlap-based transitions
- Flash, blur, shake, glitch, or beat-synced impact effects in v1
- Changing subtitle style or placement
- Changing audio timing or soundtrack selection
- Replacing MoviePy or rewriting the renderer architecture

## Design

### 1. Motion model

Each image clip should receive a subtle Ken Burns style motion treatment:

- slow zoom over the duration of the clip
- slight directional pan drift
- hard cut to the next image with no overlap

The motion should stay restrained. The goal is atmosphere, not obvious camera simulation.

Recommended default behavior:

- base zoom starts at `1.0`
- end zoom is configurable, default around `1.12`
- pan direction alternates per clip to avoid every shot moving the same way
- pan distance remains small enough that important subject matter is not pushed off frame

### 2. Configuration surface

Add config keys for cinematic motion:

- `video_motion_style`
- `video_zoom_intensity`
- `video_pan_enabled`
- `video_pan_intensity`

Expected values:

- `video_motion_style`: `static` or `cinematic`
- `video_zoom_intensity`: float-like numeric value, default `1.12`
- `video_pan_enabled`: boolean, default `true`
- `video_pan_intensity`: float-like numeric value representing a fraction of frame width, default `0.03`

Behavior:

- `static` keeps current behavior
- `cinematic` enables zoom and optional pan
- if `video_pan_enabled` is false, only the zoom effect is applied

These fields should be documented in `config.example.json` and `docs/Configuration.md`.

Example config snippet:

```json
"video_motion_style": "cinematic",
"video_zoom_intensity": 1.12,
"video_pan_enabled": true,
"video_pan_intensity": 0.03
```

### 3. Rendering integration

The motion logic should be introduced as a helper in `YouTube` rather than inline inside `combine()`.

Recommended helper shape:

- `_build_motion_clip(image_path: str, duration: float, index: int) -> VideoClip`

Responsibilities:

- load the image clip
- apply the existing crop and resize logic
- if cinematic mode is enabled, apply zoom and optional pan based on clip time and index
- return a ready-to-concatenate clip

This keeps `combine()` readable and isolates the motion rules.

### 4. Motion behavior details

The cinematic helper should:

- preserve the current 1080x1920 output size
- compute an eased zoom curve across the clip duration from `1.0` to `video_zoom_intensity`
- use a simple alternating pattern for horizontal crop drift, such as moving the crop window rightward on even clips and leftward on odd clips
- avoid randomness in v1 so renders remain testable and predictable

The motion should not change total clip duration.

Pan magnitude definition:

- `video_pan_intensity` is interpreted as a fraction of the rendered frame width
- default `0.03` means the crop window drifts by `3%` of frame width over the full clip duration
- if pan is enabled, horizontal position should drift smoothly away from center in one direction for even clips
- if pan is enabled, horizontal position should drift smoothly away from center in the opposite direction for odd clips

This makes the motion measurable and deterministic.

### 5. Safety constraints

To reduce rendering risk:

- keep motion deterministic
- do not introduce clip overlaps
- do not change subtitle timing
- keep the effect mathematically simple enough to test without pixel-level visual snapshots

If the configured zoom value is invalid or too small, the implementation should fall back to a safe default.

## Error Handling

Add safe defaults rather than failing hard on motion config mistakes.

Examples:

- unknown `video_motion_style` falls back to `static`
- invalid `video_zoom_intensity` falls back to `1.12`
- missing `video_pan_enabled` falls back to `true`
- invalid `video_pan_intensity` falls back to `0.03`

This feature should not make rendering more fragile than it is today.

## Testing

Add or update tests for:

1. config getters for the new motion settings
2. helper behavior that returns static clips when cinematic mode is disabled
3. helper behavior that applies motion when cinematic mode is enabled
4. deterministic direction selection by clip index
5. fallback behavior for invalid or missing motion settings

Tests should focus on behavior and configuration logic, not on visual-perfect output frames.

## Expected Outcome

After this change, generated Shorts should keep hard cuts but feel more cinematic because every still image has subtle motion.

Acceptance criteria:

1. static mode preserves current rendering behavior
2. cinematic mode applies an eased zoom from `1.0` to configured `video_zoom_intensity` across each clip
3. optional pan drift works without changing total duration
4. no crossfades or overlap transitions are introduced
5. configuration and docs expose the feature clearly
