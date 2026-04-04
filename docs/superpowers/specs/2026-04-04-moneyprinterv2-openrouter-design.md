# MoneyPrinterV2 OpenRouter design

## Problem

`MoneyPrinterV2` currently hardcodes Ollama for text generation:

- `src/llm_provider.py` imports and calls the local `ollama` client
- `src/main.py` expects an Ollama server and optionally prompts for a local model
- `src/cron.py` requires an Ollama model name as a positional CLI argument

This blocks use of Cristian's OpenRouter API and forces a local Ollama dependency even when a remote LLM is preferred.

## Approved direction

- Replace Ollama entirely with OpenRouter
- Use a configured default model from `config.json`
- Skip interactive model selection prompts
- Keep the internal `select_model()` / `generate_text()` interface so existing call sites do not need broader refactors

## Goals

1. Remove the runtime requirement for a local Ollama server
2. Make `python src/main.py` work with OpenRouter-only configuration
3. Make `src/cron.py` work without an Ollama model CLI arg
4. Keep the rest of the app's generation call sites unchanged
5. Fail early and clearly when OpenRouter config is missing

## Non-goals

- Supporting both Ollama and OpenRouter in the same patch
- Adding interactive OpenRouter model discovery or model-picking UI
- Refactoring unrelated generation code in `YouTube`, `Twitter`, or `AFM`

## Design

### 1. Configuration

Add these config fields:

- `openrouter_api_key`
- `openrouter_base_url`
- `openrouter_model`

Behavior:

- `openrouter_api_key` uses `config.json` first; if that value is missing or empty, fall back to `OPENROUTER_API_KEY`
- `openrouter_model` uses `config.json` first; if that value is missing or empty, fall back to `OPENROUTER_MODEL`
- `openrouter_base_url` uses `config.json` first; if that value is missing or empty, fall back to `https://openrouter.ai/api/v1`

`config.example.json` must include the new fields so the path is discoverable.

### 2. LLM provider module

`src/llm_provider.py` will stop depending on `ollama` and instead:

- keep `_selected_model`
- keep `select_model(model)` and `get_active_model()`
- remove `list_models()` because model discovery is no longer part of startup
- replace `generate_text(prompt, model_name=None)` with an OpenRouter-backed implementation

Request shape:

- `POST {openrouter_base_url}/chat/completions`
- `Authorization: Bearer <api key>`
- JSON body:
  - `model`
  - `messages: [{"role": "user", "content": prompt}]`

Response handling:

- read `choices[0].message.content`
- strip surrounding whitespace
- raise clear errors for non-200 responses, timeouts/network exceptions, empty `choices`, empty `message`, empty `content`, or malformed response bodies

Validation ownership:

- `config.py` owns value lookup and precedence
- `main.py` owns startup validation for interactive app execution
- `cron.py` owns startup validation for cron execution, including missing API key and missing model handling
- `llm_provider.py` owns request/response validation for live API calls

### 3. Main startup flow

`src/main.py` will stop doing Ollama-specific startup work.

New startup behavior:

1. fetch songs as it does today
2. validate OpenRouter API key exists
3. validate OpenRouter model exists
4. call `select_model(configured_model)`
5. print a success message showing which OpenRouter model is active

Ownership:

- `main.py` owns selecting the configured default model during normal interactive startup
- `main.py` should not delegate default-model lookup to `cron.py`

Removed behavior:

- no local Ollama connectivity check
- no `list_models()` call or local model listing path
- no interactive model selection prompt

### 4. Cron flow

`src/cron.py` will stop requiring the third CLI arg for an Ollama model.

New behavior:

- if a third arg is present, keep supporting it as an explicit model override
- otherwise `cron.py` loads the configured OpenRouter model itself and selects it
- if neither is available, exit with a clear error

This keeps cron usable while making config-driven OpenRouter the default path.

### 5. Setup and documentation surfaces

This migration is not complete unless these Ollama-shaped setup surfaces are updated too:

- `requirements.txt` — remove the `ollama` dependency if no code imports it anymore
- `scripts/setup_local.sh` — stop auto-configuring local Ollama defaults and instead seed OpenRouter fields
- `scripts/preflight_local.py` — use the same config→env precedence as runtime, validate key/model presence, and perform a lightweight OpenRouter reachability check instead of probing a local Ollama server
- `README.md` and `docs/Configuration.md` — replace Ollama setup guidance with OpenRouter configuration
- `docs/AffiliateMarketing.md` and `CLAUDE.md` — remove stale claims that LLM usage is Ollama-only
- remove obsolete Ollama-only config/docs references rather than leaving them as alternate paths

Migration contract for old config state:

- runtime code no longer reads `ollama_base_url`, `ollama_model`, or `llm_provider=local_ollama`
- existing user configs may still contain those old keys, but they are ignored
- `config.example.json` and setup scripts should stop generating those old Ollama keys
- repo docs should describe OpenRouter as the only supported LLM backend after this patch

If `main.py` still passes an explicit model to cron anywhere in the repo, that call site should remain valid as an override, but default behavior should come from config.

## Error handling

Fail fast with explicit messages for:

- missing OpenRouter API key
- missing OpenRouter model
- HTTP errors from OpenRouter
- timeouts or connection failures when calling OpenRouter
- unexpected/malformed OpenRouter responses

Per-call behavior:

- `generate_text(prompt, model_name=None)` keeps supporting a per-call `model_name` override
- if `model_name` is absent, `generate_text()` uses the selected default model from `select_model()`
- there is no silent fallback to removed Ollama settings

No silent fallback to Ollama or any other provider.

## Testing

Add or update tests for:

1. config accessors for `openrouter_api_key`, `openrouter_base_url`, and `openrouter_model`
   - configured value wins over env/default
   - empty config value falls back to env/default
   - missing config value falls back to env/default
2. `llm_provider.generate_text()` making the expected OpenRouter request and parsing the reply
   - includes regression coverage for `model_name=` per-call override behavior
3. `main.py` importing and initializing with OpenRouter config and no Ollama dependency
4. `cron.py` using configured model defaults when no CLI override is passed
5. startup/import coverage that passes without the `ollama` module being present in `sys.modules`
6. startup/cron error coverage for missing API key and missing configured model
7. updates for existing Ollama-shaped integration tests/surfaces, including `tests/test_startup_imports.py`, `tests/test_cron_post_bridge.py`, and any `main.py` cron command construction paths

Test doubles are acceptable for the HTTP boundary, but tests should verify app behavior rather than mock existence.

## Implementation notes

- Prefer `requests` over adding a new OpenAI/OpenRouter SDK dependency
- Use a single request timeout value (60s) and do not add retries in this patch
- Preserve the existing `generate_text(prompt, model_name=None)` call signature
- Keep changes scoped to config, startup, cron, and provider wiring

## Expected outcome

After this change, MoneyPrinterV2 should be able to run with:

- an OpenRouter API key
- a configured OpenRouter model
- no local Ollama server or Ollama model pulls

Acceptance criteria:

1. `python src/main.py` no longer checks Ollama or prompts for Ollama models
2. `python src/main.py` exits early with a clear error if OpenRouter key or model is missing
3. `python src/main.py` starts with a configured OpenRouter model and no local Ollama server
4. `python src/cron.py <purpose> <account_id>` works without a third model arg when config supplies `openrouter_model`
5. `python src/cron.py <purpose> <account_id> <model>` keeps treating the third arg as an explicit override
6. any cron command strings emitted by `main.py` switch to the 2-arg default path unless an explicit override is intentionally desired
