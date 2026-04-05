# YouTube Script Detailing Design

## Problem

The current YouTube Shorts script generation is optimized for very short, low-detail output:

- `config.json` sets `script_sentence_length` to `4`
- `YouTube.generate_script()` in `src/classes/YouTube.py` tells the model to keep the script within that sentence count
- the prompt also says the sentences must be short

That combination pushes the model toward shallow, summary-style scripts instead of strong story-driven Shorts.

## Approved Direction

- Keep script length configurable
- Increase the default sentence count from `4` to `6`
- Replace the generic script prompt with a story-structured prompt
- Optimize the prompt for the active niche: strange real events, unexplained cases, disasters, and historical incidents that sound fictional
- Keep the final output plain text with no title, labels, markdown, or speaker prefixes

## Goals

1. Produce denser Shorts scripts with more context and clearer story beats
2. Preserve pacing suitable for YouTube Shorts rather than drifting into long-form narration
3. Improve hooks, escalation, and endings for faceless AI-image storytelling
4. Keep the implementation small and local to config, prompt generation, and prompt-focused tests

## Non-goals

- Adding a second long-form script mode
- Changing TTS, image generation, or subtitle rendering
- Building a full niche-to-prompt template system for all content categories
- Refactoring unrelated YouTube generation code

## Design

### 1. Script length default

Update `config.json` so the existing key changes from:

```json
"script_sentence_length": 4
```

to:

```json
"script_sentence_length": 6
```

Rationale:

- `6` sentences gives enough room for hook, setup, escalation, and payoff
- it is still short enough to remain viable for Shorts pacing
- it avoids turning the script into a miniature explainer article

### 2. Story-structured script prompt

`YouTube.generate_script()` should stop asking for a generic script and instead ask for a structured short-form story.

The code should use a concrete prompt template in this shape:

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

Use this beat structure as closely as possible:
1. Hook with the strangest or most unsettling claim.
2. Ground the story with who, where, or when.
3. Explain the core anomaly, disaster, or impossible-seeming detail.
4. Escalate with consequence, discovery, or rising tension.
5. Deliver the main reveal, confirmed outcome, or historical consequence.
6. End with a final sting, unresolved mystery, or haunting closing fact.
```

The prompt should instruct the model to produce exactly `N` sentences, where each sentence has a job:

1. Hook with the most surprising or unsettling claim
2. Establish who, where, or when
3. Explain the strange detail or core anomaly
4. Escalate with consequence, complication, or discovery
5. Deliver the main reveal, consequence, or confirmed outcome
6. End with a sting, unresolved question, or haunting closing fact

If `N` is not `6`, the prompt should still preserve the same principles:

- every sentence must advance the story
- no filler, introductions, or summary language
- keep the voice direct and cinematic

Dynamic beat mapping rules:

- `4` sentences: combine beats `2` and `3`, and combine beats `5` and `6`
- `5` sentences: keep beats `1` through `5`, with beat `5` including the sting element
- `6` sentences: use the full beat structure unchanged
- `7+` sentences: preserve beats `1` through `6` and use extra sentences only for concrete escalation details between beats `3` and `5`

Mandatory beats regardless of sentence count:

- opening hook
- grounding context
- anomaly/disaster detail
- reveal or consequence
- strong closing line

### 3. Detail requirements

The prompt should explicitly favor:

- concrete details over generic wording
- real-event storytelling tone
- clear sequencing of events
- strong ending lines that feel unresolved, eerie, or consequential

The prompt should explicitly avoid:

- “welcome back” or other intro filler
- listicle tone
- vague “did you know” phrasing
- broad educational framing when a dramatic framing is possible

### 4. Output constraints

The script generator should continue enforcing:

- raw text only
- no markdown
- no title
- no speaker labels
- no prompt leakage

The regex cleanup that strips `*` can remain unchanged unless tests show that the new prompt requires broader output cleanup.

## Error Handling

No new error pathways are required for this change.

Existing protections remain acceptable:

- empty completion handling
- recursive retry if script output exceeds the hard length threshold

Output cleanup boundary:

- keep the existing `*` stripping in place
- do not add broader cleanup unless tests or live output show a repeated formatting issue such as leading code fences, title prefixes, or speaker labels
- if that happens, cleanup should remain minimal and targeted rather than becoming a general parser

## Testing

Add or update prompt-focused tests to verify:

1. the generated script prompt now encodes the story-beat structure
2. the configured sentence length is still injected into the prompt
3. the prompt no longer tells the model to make every sentence short
4. the prompt still requires plain raw script output with no formatting

Testing location:

- update `tests/test_youtube_prompt_generation.py`
- keep using the existing Python `unittest` style already used in the repo
- assertions should inspect the constructed prompt text and confirm that the required story-beat instructions and raw-output constraints are present

Runtime tests do not need major expansion unless prompt construction is refactored into helpers.

## Expected Outcome

After this change, generated Shorts scripts should feel more like compact narrated stories and less like compressed summaries.

Acceptance criteria:

1. default script length is `6` sentences
2. script prompt explicitly asks for story progression and concrete details
3. script prompt is aligned with the current storytelling niche
4. generated script output remains plain text and short-form compatible