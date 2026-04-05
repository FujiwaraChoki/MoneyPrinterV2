# YouTube Script Detailing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated YouTube Shorts scripts more detailed by increasing the default sentence count and replacing the generic script prompt with a story-structured prompt tailored to the current storytelling niche.

**Architecture:** Keep the change local to prompt construction and config defaults. Update the active default in `config.json`, rewrite `YouTube.generate_script()` so the prompt encodes story beats and stronger detail requirements, and extend prompt-generation tests to lock in the new behavior.

**Tech Stack:** Python 3.12, `unittest`, JSON config, existing MoneyPrinterV2 YouTube generation flow

---

## File map

- Modify: `config.json` — change the default `script_sentence_length` from `4` to `6`.
- Modify: `src/classes/YouTube.py` — replace the generic `generate_script()` prompt with a story-structured prompt.
- Modify: `tests/test_youtube_prompt_generation.py` — add prompt-generation coverage for the new structure and constraints.
- Reference: `docs/superpowers/specs/2026-04-04-youtube-script-detailing-design.md` — approved design spec for the exact prompt requirements and beat mapping rules.

## Chunk 1: Prompt coverage first

### Task 1: Add failing tests for detailed story prompt generation

**Files:**
- Modify: `tests/test_youtube_prompt_generation.py`

- [ ] **Step 0: Pre-flight sanity check**

Verify before editing:
- `config.json` contains the `script_sentence_length` key
- `YouTube.generate_script()` exists in `src/classes/YouTube.py`

Run:

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
rg "script_sentence_length" config.json src/classes/YouTube.py
```

Expected: one match in `config.json` and at least one match in `src/classes/YouTube.py`.

- [ ] **Step 1: Add a prompt-capture test for `generate_script()`**

Add a new test method that:
- creates a `YouTube` instance with `__new__`
- sets `subject` and `_language`
- patches `get_script_sentence_length()` to return `6`
- stubs `generate_response()` to return a short fake script
- calls `generate_script()`
- captures the prompt passed into `generate_response()`

Use this test shape:

```python
def test_generate_script_uses_story_structured_prompt(self) -> None:
    youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
    youtube.subject = "The ship that disappeared overnight"
    youtube._language = "english"

    youtube.generate_response = Mock(
        return_value=(
            "A ship vanished without a trace. "
            "It had left port the night before. "
            "The strangest detail was what crews found next. "
            "Search teams kept uncovering new clues. "
            "The final report only deepened the mystery. "
            "No one ever explained the last signal."
        )
    )

    with patch.object(self.youtube_module, "get_script_sentence_length", return_value=6):
        script = youtube.generate_script()

    prompt = youtube.generate_response.call_args.args[0]

    self.assertEqual(script, youtube.script)
    self.assertIn("exactly 6 sentences", prompt)
    self.assertIn("compact narrated story", prompt)
    self.assertIn("Every sentence must add a new concrete detail", prompt)
    self.assertIn("Hook with the strangest or most unsettling claim", prompt)
    self.assertIn("End with a final sting", prompt)
```

- [ ] **Step 2: Add a test that the prompt preserves raw-output constraints**

Add a second test that verifies the prompt still forbids formatting and speaker labels.

Use this shape:

```python
def test_generate_script_prompt_preserves_raw_output_constraints(self) -> None:
    youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
    youtube.subject = "A town heard the same sound every night"
    youtube._language = "english"
    youtube.generate_response = Mock(return_value="One. Two. Three. Four. Five. Six.")

    with patch.object(self.youtube_module, "get_script_sentence_length", return_value=6):
        youtube.generate_script()

    prompt = youtube.generate_response.call_args.args[0]

    self.assertIn("Do not use markdown", prompt)
    self.assertIn("Do not use filler", prompt)
    self.assertIn("Do not say things like \"welcome back\"", prompt)
    self.assertIn("Return only the raw script", prompt)
    self.assertNotIn("SENTENCES ARE SHORT", prompt)
```

- [ ] **Step 2a: Add a test that sentence count remains dynamic**

Add a third test that patches `get_script_sentence_length()` to return `5` and verifies the prompt says `exactly 5 sentences` so the implementation does not hardcode `6` in the prompt body.

Use this shape:

```python
def test_generate_script_prompt_uses_configured_sentence_count(self) -> None:
    youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
    youtube.subject = "A city woke up covered in ash"
    youtube._language = "english"
    youtube.generate_response = Mock(return_value="One. Two. Three. Four. Five.")

    with patch.object(self.youtube_module, "get_script_sentence_length", return_value=5):
        youtube.generate_script()

    prompt = youtube.generate_response.call_args.args[0]

    self.assertIn("exactly 5 sentences", prompt)
```

- [ ] **Step 3: Run the focused tests and verify they fail**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_youtube_prompt_generation -v`

Expected: FAIL because the current prompt does not contain the new story-structure language.

## Chunk 2: Minimal implementation

### Task 2: Update the default script length

**Files:**
- Modify: `config.json`

- [ ] **Step 1: Change the config default**

Update:

```json
"script_sentence_length": 4
```

to:

```json
"script_sentence_length": 6
```

- [ ] **Step 2: Verify the config file remains valid JSON**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && python -m json.tool config.json >/dev/null`

Expected: command exits successfully with no output.

### Task 3: Replace the generic script prompt with a story-structured prompt

**Files:**
- Modify: `src/classes/YouTube.py`

- [ ] **Step 1: Rewrite the `generate_script()` prompt text only**

Inside `YouTube.generate_script()`, replace the existing multiline prompt with a new one that:
- says `Generate a script for a YouTube Short in exactly {sentence_length} sentences`
- includes `Subject: {self.subject}`
- includes `Language: {self.language}`
- includes the storytelling niche text directly
- instructs the model to write a compact narrated story about a real event
- requires every sentence to add a concrete detail or move the story forward
- forbids filler, listicle framing, generic educational intros, markdown, title text, and speaker labels
- includes the 6-beat story structure

Use this exact beat language in the prompt body:

```text
1. Hook with the strangest or most unsettling claim.
2. Ground the story with who, where, or when.
3. Explain the core anomaly, disaster, or impossible-seeming detail.
4. Escalate with consequence, discovery, or rising tension.
5. Deliver the main reveal, confirmed outcome, or historical consequence.
6. End with a final sting, unresolved mystery, or haunting closing fact.
```

Keep the rest of the method behavior unchanged:
- still call `get_script_sentence_length()`
- still use `self.generate_response(prompt)`
- still strip `*`
- still retry if script length exceeds the hard cap

Use a prompt structure that closely follows this wording so it satisfies the tests and stays aligned with the approved spec:

```text
Generate a script for a YouTube Short in exactly {sentence_length} sentences.

The subject is: {self.subject}
The language is: {self.language}
The niche is: strange real events, unexplained cases, disasters, and historical incidents that sound fictional.

Write the script like a compact narrated story about a real event.
Every sentence must add a new concrete detail or move the story forward.
Do not use filler, introductions, conclusions, listicles, or educational framing.
Do not say things like "welcome back", "in this video", or "did you know".
Do not use markdown, titles, bullet points, speaker labels, or quotation marks around the full response.
Return only the raw script.
```

- [ ] **Step 2: Run the focused prompt tests and verify they pass**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_youtube_prompt_generation -v`

Expected: PASS.

## Chunk 3: Regression verification

### Task 4: Run the existing related regression slice

**Files:**
- No additional file changes

- [ ] **Step 1: Run the related regression tests**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && ./venv/bin/python -m unittest tests.test_youtube_prompt_generation tests.test_youtube_image_provider tests.test_main_runtime -v`

Expected: PASS.

- [ ] **Step 2: Optionally smoke-test one generated script manually**

Run: `cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter && python src/main.py`

Manual check:
- generate one YouTube script
- confirm it feels denser than the previous 4-sentence output
- confirm pacing still feels Shorts-compatible

If Firefox startup blocks the full run again, treat the automated regression slice as the required verification for this patch and note the existing browser startup issue separately.

- [ ] **Step 3: Commit**

```bash
cd /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter
git add config.json src/classes/YouTube.py tests/test_youtube_prompt_generation.py docs/superpowers/specs/2026-04-04-youtube-script-detailing-design.md docs/superpowers/plans/2026-04-04-youtube-script-detailing.md
git commit -m "feat: generate more detailed youtube short scripts"
```