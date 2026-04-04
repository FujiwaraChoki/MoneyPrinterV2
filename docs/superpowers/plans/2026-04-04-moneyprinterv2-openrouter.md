# MoneyPrinterV2 OpenRouter Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Ollama with a config-driven OpenRouter backend across MoneyPrinterV2 runtime, cron, setup, and docs without changing existing generation call sites.

**Architecture:** Keep the existing `select_model()` / `generate_text()` API surface, but rewire it to OpenRouter via `requests`. Move config precedence into `src/config.py`, let `src/main.py` and `src/cron.py` own early validation, and update setup/preflight/docs so the repo no longer assumes a local Ollama server.

**Tech Stack:** Python 3.12, `requests`, `unittest`, shell scripts, JSON config

---

## File map

- Modify: `config.example.json` — replace Ollama example keys with OpenRouter keys.
- Modify: `requirements.txt` — remove `ollama` dependency if no code imports remain.
- Modify: `src/config.py:72-90` — replace Ollama getters with OpenRouter getters and precedence logic.
- Modify: `src/llm_provider.py:1-64` — replace Ollama client calls with OpenRouter HTTP calls.
- Modify: `src/main.py:204-206,335-336,440-490` — extract testable startup/cron helpers, remove Ollama startup/model-prompt logic, and switch scheduled cron commands to config-default behavior.
- Modify: `src/cron.py:31-39` — make config-backed OpenRouter model selection the default and keep CLI model override support.
- Modify: `scripts/setup_local.sh:37-112` — seed OpenRouter config instead of Ollama defaults.
- Modify: `scripts/preflight_local.py:34-120` — validate OpenRouter config and reachability instead of Ollama.
- Modify: `docs/Configuration.md` — document OpenRouter config fields and env fallbacks.
- Modify: `README.md` — replace Ollama setup/run guidance with OpenRouter guidance.
- Modify: `docs/AffiliateMarketing.md` — remove Ollama-only wording.
- Modify: `CLAUDE.md` — remove Ollama-only setup guidance.
- Modify: `tests/test_config.py` — add OpenRouter config precedence coverage.
- Modify: `tests/test_startup_imports.py` — make startup import coverage use OpenRouter config and no `ollama` module.
- Create: `tests/test_main_runtime.py` — cover extracted startup/bootstrap and cron command helpers.
- Modify: `tests/test_cron_post_bridge.py` — cover default-model path and CLI override path without Ollama assumptions.
- Create: `tests/test_llm_provider.py` — cover OpenRouter request/response handling and per-call model override behavior.
- Create: `tests/test_preflight_local.py` — cover OpenRouter preflight precedence and failure modes.

## Chunk 1: Core config and provider wiring

### Task 1: Add OpenRouter config accessors

**Files:**
- Modify: `src/config.py:72-90`
- Modify: `tests/test_config.py`
- Modify: `config.example.json`

- [ ] **Step 1: Write the failing config tests**

```python
class OpenRouterConfigTests(unittest.TestCase):
    def write_config(self, directory: str, payload: dict) -> None:
        with open(os.path.join(directory, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def test_openrouter_model_uses_config_value_before_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_model": "openai/gpt-4.1-mini"})
            with patch.dict(os.environ, {"OPENROUTER_MODEL": "ignored/model"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_model(), "openai/gpt-4.1-mini")

    def test_openrouter_model_falls_back_to_env_when_config_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_model": ""})
            with patch.dict(os.environ, {"OPENROUTER_MODEL": "google/gemini-2.5-flash-lite-preview-09-2025"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_model(), "google/gemini-2.5-flash-lite-preview-09-2025")

    def test_openrouter_api_key_falls_back_to_env_when_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_api_key(), "env-key")

    def test_openrouter_api_key_falls_back_to_env_when_config_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_api_key": ""})
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_api_key(), "env-key")

    def test_openrouter_base_url_uses_default_when_config_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_base_url": ""})
            with patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(
                    config.get_openrouter_base_url(),
                    "https://openrouter.ai/api/v1",
                )

    def test_openrouter_api_key_uses_config_value_before_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_api_key": "config-key"})
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_api_key(), "config-key")

    def test_openrouter_api_key_falls_back_to_empty_when_missing_everywhere(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})
            with patch.dict(os.environ, {}, clear=True), patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_api_key(), "")

    def test_openrouter_model_falls_back_to_empty_when_missing_everywhere(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})
            with patch.dict(os.environ, {}, clear=True), patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_model(), "")

    def test_openrouter_model_falls_back_to_env_when_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})
            with patch.dict(os.environ, {"OPENROUTER_MODEL": "env-model"}, clear=False), \
                 patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(config.get_openrouter_model(), "env-model")

    def test_openrouter_base_url_uses_config_value_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"openrouter_base_url": "https://openrouter.example/api/v1"})
            with patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(
                    config.get_openrouter_base_url(),
                    "https://openrouter.example/api/v1",
                )

    def test_openrouter_base_url_uses_default_when_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})
            with patch.object(config, "ROOT_DIR", temp_dir):
                self.assertEqual(
                    config.get_openrouter_base_url(),
                    "https://openrouter.ai/api/v1",
                )
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_config.OpenRouterConfigTests -v`

Expected: FAIL with missing `get_openrouter_*` accessors.

- [ ] **Step 3: Implement minimal OpenRouter getters in `src/config.py`**

```python
def get_openrouter_api_key() -> str:
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        configured = json.load(file).get("openrouter_api_key", "")
        return configured or os.environ.get("OPENROUTER_API_KEY", "")
```

Also add:
- `get_openrouter_model()` with config-first, env-second, empty-string fallback behavior
- `get_openrouter_base_url()` with config-first, default-second behavior
- keep the existing `get_ollama_base_url()` / `get_ollama_model()` getters untouched in this chunk so Chunk 1 does not break `main.py` before Chunk 2

- [ ] **Step 4: Update `config.example.json`**

Add:

```json
"openrouter_api_key": "",
"openrouter_base_url": "https://openrouter.ai/api/v1",
"openrouter_model": ""
```

Remove the old Ollama fields from the example file: `ollama_base_url` and `ollama_model`.

- [ ] **Step 5: Re-run the config tests**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_config.OpenRouterConfigTests -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add config.example.json src/config.py tests/test_config.py
git commit -m "feat: add openrouter config accessors"
```

### Task 2: Replace Ollama client calls with OpenRouter HTTP calls

**Files:**
- Modify: `src/llm_provider.py:1-64`
- Create: `tests/test_llm_provider.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Write the failing provider tests**

```python
class OpenRouterProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        llm_provider._selected_model = None

    @patch("llm_provider.get_openrouter_api_key", return_value="test-key")
    @patch("llm_provider.get_openrouter_base_url", return_value="https://openrouter.ai/api/v1")
    @patch("llm_provider.requests.post")
    def test_generate_text_posts_to_openrouter(
        self,
        post_mock,
        _base_url_mock,
        _api_key_mock,
    ) -> None:
        post_mock.return_value.json.return_value = {
            "choices": [{"message": {"content": " Hello world "}}]
        }
        post_mock.return_value.raise_for_status.return_value = None

        llm_provider.select_model("openai/gpt-4.1-mini")
        result = llm_provider.generate_text("Say hello")

        self.assertEqual(result, "Hello world")
        post_mock.assert_called_once()
        self.assertEqual(
            post_mock.call_args.args[0],
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(
            post_mock.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )
```

On the same `OpenRouterProviderTests` class, add concrete companion methods:

```python
    def test_generate_text_requires_selected_model(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "No OpenRouter model selected"):
            llm_provider.generate_text("Say hello")

    @patch("llm_provider.get_openrouter_api_key", return_value="test-key")
    @patch("llm_provider.get_openrouter_base_url", return_value="https://openrouter.ai/api/v1")
    @patch("llm_provider.requests.post")
    def test_generate_text_model_name_override_wins(
        self,
        post_mock,
        _base_url_mock,
        _api_key_mock,
    ) -> None:
        post_mock.return_value.json.return_value = {
            "choices": [{"message": {"content": "Override"}}]
        }
        post_mock.return_value.raise_for_status.return_value = None
        llm_provider.select_model("default/model")
        llm_provider.generate_text("Say hello", model_name="override/model")
        self.assertEqual(post_mock.call_args.kwargs["json"]["model"], "override/model")

    @patch("llm_provider.get_openrouter_api_key", return_value="test-key")
    @patch("llm_provider.get_openrouter_base_url", return_value="https://openrouter.ai/api/v1")
    @patch("llm_provider.requests.post", side_effect=requests.Timeout("boom"))
    def test_generate_text_wraps_timeout_errors(
        self,
        _post_mock,
        _base_url_mock,
        _api_key_mock,
    ) -> None:
        llm_provider.select_model("openai/gpt-4.1-mini")
        with self.assertRaisesRegex(RuntimeError, "OpenRouter request failed"):
            llm_provider.generate_text("Say hello")

    @patch("llm_provider.get_openrouter_api_key", return_value="test-key")
    @patch("llm_provider.get_openrouter_base_url", return_value="https://openrouter.ai/api/v1")
    @patch("llm_provider.requests.post")
    def test_generate_text_rejects_empty_choices(
        self,
        post_mock,
        _base_url_mock,
        _api_key_mock,
    ) -> None:
        post_mock.return_value.json.return_value = {"choices": []}
        post_mock.return_value.raise_for_status.return_value = None
        llm_provider.select_model("openai/gpt-4.1-mini")
        with self.assertRaisesRegex(RuntimeError, "OpenRouter response did not include choices"):
            llm_provider.generate_text("Say hello")
```

Add separate, explicit `unittest.TestCase` methods for:
- missing API key raising `RuntimeError` with the exact OpenRouter-specific error text
- `raise_for_status()` HTTP failures being wrapped as `RuntimeError`
- `requests.Timeout` / `requests.RequestException`
- `.json()` returning a non-dict payload
- `.json()` raising `ValueError`
- missing `message`
- missing `content`

- [ ] **Step 2: Run the provider tests to verify they fail**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_llm_provider -v`

Expected: FAIL because `llm_provider` still imports `ollama`.

- [ ] **Step 3: Implement the minimal OpenRouter provider**

```python
response = requests.post(
    f"{get_openrouter_base_url().rstrip('/')}/chat/completions",
    headers={"Authorization": f"Bearer {get_openrouter_api_key()}"},
    json={"model": model, "messages": [{"role": "user", "content": prompt}]},
    timeout=60,
)
```

Implementation requirements:
- keep `_selected_model`, `select_model()`, `get_active_model()`, and `generate_text(prompt, model_name=None)`
- keep a temporary `list_models()` compatibility shim that raises a clear `RuntimeError` until Chunk 2 removes `main.py`'s import path
- raise explicit `RuntimeError` messages for missing API key, missing model, empty/malformed responses, and network/timeout failures

- [ ] **Step 4: Remove the Ollama dependency**

Delete `ollama` from `requirements.txt` if no code imports it after this task.

- [ ] **Step 5: Re-run the provider tests**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_llm_provider tests.test_startup_imports -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add requirements.txt src/llm_provider.py tests/test_llm_provider.py
git commit -m "feat: swap llm provider to openrouter"
```

## Chunk 2: Startup and cron migration

### Task 3: Make interactive startup use configured OpenRouter defaults

**Files:**
- Modify: `src/main.py:440-490`
- Modify: `tests/test_startup_imports.py`
- Create: `tests/test_main_runtime.py`

- [ ] **Step 1: Write the failing startup tests**

Extend `tests/test_startup_imports.py` so the temp config includes:

```python
example_config["openrouter_api_key"] = "test-key"
example_config["openrouter_model"] = "openai/gpt-4.1-mini"
example_config.pop("ollama_base_url", None)
example_config.pop("ollama_model", None)
```

Add assertions that importing `main` succeeds without an `ollama` module present in `sys.modules`.

Create `tests/test_main_runtime.py` with concrete bootstrap tests:

```python
class MainRuntimeTests(unittest.TestCase):
    @patch("main.fetch_songs")
    @patch("main.select_model")
    @patch("main.success")
    @patch("main.get_openrouter_model", return_value="openai/gpt-4.1-mini")
    @patch("main.get_openrouter_api_key", return_value="test-key")
    def test_bootstrap_runtime_selects_configured_openrouter_model(
        self,
        _get_key_mock,
        _get_model_mock,
        success_mock,
        select_model_mock,
        fetch_songs_mock,
    ) -> None:
        main.bootstrap_runtime()
        fetch_songs_mock.assert_called_once()
        select_model_mock.assert_called_once_with("openai/gpt-4.1-mini")
        success_mock.assert_called_once_with(
            "Using configured OpenRouter model: openai/gpt-4.1-mini"
        )

    @patch("main.fetch_songs")
    @patch("main.error")
    @patch("main.get_openrouter_model", return_value="openai/gpt-4.1-mini")
    @patch("main.get_openrouter_api_key", return_value="")
    def test_bootstrap_runtime_exits_when_api_key_missing(
        self,
        _get_key_mock,
        _get_model_mock,
        error_mock,
        _fetch_songs_mock,
    ) -> None:
        with self.assertRaises(SystemExit):
            main.bootstrap_runtime()
        error_mock.assert_called_once_with(
            "No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY."
        )

    @patch("main.fetch_songs")
    @patch("main.error")
    @patch("main.get_openrouter_model", return_value="")
    @patch("main.get_openrouter_api_key", return_value="test-key")
    def test_bootstrap_runtime_exits_when_model_missing(
        self,
        _get_key_mock,
        _get_model_mock,
        error_mock,
        _fetch_songs_mock,
    ) -> None:
        with self.assertRaises(SystemExit):
            main.bootstrap_runtime()
        error_mock.assert_called_once_with(
            "No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL."
        )
```

- [ ] **Step 2: Run the startup tests to verify they fail**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_startup_imports tests.test_main_runtime -v`

Expected: FAIL because `main.py` still imports `list_models()` / `get_ollama_model()` and has no `bootstrap_runtime()`.

- [ ] **Step 3: Implement the minimal startup change**

Extract the startup block into a testable helper:

```python
def bootstrap_runtime() -> None:
    fetch_songs()
    configured_model = get_openrouter_model()
    if not get_openrouter_api_key():
        error("No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.")
        sys.exit(1)
    if not configured_model:
        error("No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.")
        sys.exit(1)
    select_model(configured_model)
    success(f"Using configured OpenRouter model: {configured_model}")
```

Then call `bootstrap_runtime()` from the `if __name__ == "__main__":` path and remove all `list_models` / `get_ollama_model` imports/usages from `main.py`.

- [ ] **Step 4: Re-run the startup tests**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_startup_imports tests.test_main_runtime -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add src/main.py tests/test_startup_imports.py tests/test_main_runtime.py
git commit -m "feat: use openrouter config during startup"
```

### Task 4: Make cron config-driven by default and preserve CLI override

**Files:**
- Modify: `src/cron.py:31-39`
- Modify: `src/main.py:204-206,335-336`
- Modify: `tests/test_cron_post_bridge.py`
- Modify: `tests/test_main_runtime.py`

- [ ] **Step 1: Write the failing cron tests**

Add concrete cron tests:

```python
class CronPostBridgeTests(unittest.TestCase):
    @patch("cron.maybe_crosspost_youtube_short")
    @patch("cron.YouTube")
    @patch("cron.TTS")
    @patch("cron.get_accounts")
    @patch("cron.get_verbose")
    @patch("cron.get_openrouter_api_key", return_value="test-key")
    @patch("cron.get_openrouter_model", return_value="openai/gpt-4.1-mini")
    @patch("cron.select_model")
    def test_cron_uses_configured_model_when_cli_override_missing(
        self,
        select_model_mock,
        _get_model_mock,
        _get_key_mock,
        get_verbose_mock,
        get_accounts_mock,
        tts_cls_mock,
        youtube_cls_mock,
        crosspost_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_accounts_mock.return_value = [{"id": "yt-1", "nickname": "Channel", "firefox_profile": "/tmp/profile", "niche": "finance", "language": "English"}]
        youtube_cls_mock.return_value.upload_video.return_value = False
        youtube_cls_mock.return_value.video_path = "/tmp/video.mp4"
        youtube_cls_mock.return_value.metadata = {"title": "Title"}
        with patch.object(sys, "argv", ["cron.py", "youtube", "yt-1"]):
            cron.main()
        select_model_mock.assert_called_once_with("openai/gpt-4.1-mini")

    @patch("cron.maybe_crosspost_youtube_short")
    @patch("cron.YouTube")
    @patch("cron.TTS")
    @patch("cron.get_accounts")
    @patch("cron.get_verbose")
    @patch("cron.get_openrouter_api_key", return_value="test-key")
    @patch("cron.get_openrouter_model", return_value="openai/gpt-4.1-mini")
    @patch("cron.select_model")
    def test_cli_model_override_wins_over_config(
        self,
        select_model_mock,
        _get_model_mock,
        _get_key_mock,
        get_verbose_mock,
        get_accounts_mock,
        tts_cls_mock,
        youtube_cls_mock,
        crosspost_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_accounts_mock.return_value = [{"id": "yt-1", "nickname": "Channel", "firefox_profile": "/tmp/profile", "niche": "finance", "language": "English"}]
        youtube_cls_mock.return_value.upload_video.return_value = False
        youtube_cls_mock.return_value.video_path = "/tmp/video.mp4"
        youtube_cls_mock.return_value.metadata = {"title": "Title"}
        with patch.object(sys, "argv", ["cron.py", "youtube", "yt-1", "override/model"]):
            cron.main()
        select_model_mock.assert_called_once_with("override/model")

    @patch("cron.get_accounts", return_value=[])
    @patch("cron.error")
    @patch("cron.get_openrouter_model", return_value="openai/gpt-4.1-mini")
    @patch("cron.get_openrouter_api_key", return_value="")
    def test_cron_exits_when_api_key_missing(self, _get_key_mock, _get_model_mock, error_mock, _accounts_mock) -> None:
        with patch.object(sys, "argv", ["cron.py", "youtube", "yt-1"]), self.assertRaises(SystemExit):
            cron.main()
        error_mock.assert_called_once_with(
            "No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY."
        )
```

Add cron error-path tests for missing API key and missing configured model.

In `tests/test_main_runtime.py`, add explicit command-builder coverage by first extracting a helper from `main.py`:

```python
def test_build_cron_command_uses_two_arg_default_path(self) -> None:
    self.assertEqual(
        main.build_cron_command("youtube", "yt-1"),
        ["python", os.path.join(main.ROOT_DIR, "src", "cron.py"), "youtube", "yt-1"],
    )
```

- [ ] **Step 2: Run the cron tests to verify they fail**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_cron_post_bridge -v`

Expected: FAIL because `cron.py` exits when the third CLI arg is missing and `main.py` has no `build_cron_command()` helper.

- [ ] **Step 3: Implement minimal cron/default-model behavior**

```python
model = str(sys.argv[3]) if len(sys.argv) > 3 else get_openrouter_model()
if not get_openrouter_api_key():
    error("No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.")
    sys.exit(1)
if not model:
    error("No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.")
    sys.exit(1)
select_model(model)
```

Add a small helper in `main.py`:

```python
def build_cron_command(purpose: str, account_id: str, model: str | None = None) -> list[str]:
    command = ["python", os.path.join(ROOT_DIR, "src", "cron.py"), purpose, account_id]
    if model:
        command.append(model)
    return command
```

Update `src/main.py` scheduled job commands from:

```python
["python", cron_script_path, "youtube", selected_account["id"], get_active_model()]
```

to:

```python
["python", cron_script_path, "youtube", selected_account["id"]]
```

and the analogous Twitter path.

- [ ] **Step 4: Re-run the cron tests**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_cron_post_bridge tests.test_main_runtime -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add src/cron.py src/main.py tests/test_cron_post_bridge.py tests/test_main_runtime.py
git commit -m "feat: default cron to configured openrouter model"
```

## Chunk 3: Setup, preflight, and documentation cleanup

### Task 5: Update local setup and preflight scripts

**Files:**
- Modify: `scripts/setup_local.sh:37-115`
- Modify: `scripts/preflight_local.py:34-120`
- Create: `tests/test_preflight_local.py`

- [ ] **Step 1: Write the failing preflight tests**

Add tests covering:
- config value wins over defaults for OpenRouter fields
- config value wins over env for `openrouter_api_key` and `openrouter_model`
- empty config falls back to env for `openrouter_api_key` and `openrouter_model`
- empty config falls back to the documented default base URL
- missing key/model produces blocking failures
- reachability checks hit the OpenRouter base URL, not `127.0.0.1:11434`

Example tests:

```python
class PreflightLocalTests(unittest.TestCase):
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=True)
    @patch("preflight_local.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{\"openrouter_api_key\": \"\", \"openrouter_model\": \"openai/gpt-4.1-mini\", \"openrouter_base_url\": \"\"}')
    @patch("preflight_local.requests.get")
    def test_openrouter_api_key_falls_back_to_env(
        self,
        get_mock,
        _open_mock,
        _exists_mock,
    ) -> None:
        get_mock.return_value.status_code = 200
        get_mock.return_value.json.return_value = {"data": []}
        self.assertEqual(preflight_local.main(), 0)

    @patch("preflight_local.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{\"openrouter_api_key\": \"config-key\", \"openrouter_model\": \"openai/gpt-4.1-mini\", \"openrouter_base_url\": \"https://openrouter.ai/api/v1\"}')
    @patch("preflight_local.requests.get")
    def test_reachability_check_uses_openrouter_models_endpoint(
        self,
        get_mock,
        _open_mock,
        _exists_mock,
    ) -> None:
        get_mock.return_value.status_code = 200
        get_mock.return_value.json.return_value = {"data": []}
        preflight_local.main()
        self.assertTrue(any(call.args[0].endswith("/models") for call in get_mock.call_args_list))
```

- [ ] **Step 2: Run the preflight tests to verify they fail**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_preflight_local -v`

Expected: FAIL because preflight still probes Ollama.

- [ ] **Step 3: Implement minimal setup/preflight changes**

In `scripts/setup_local.sh`:
- stop writing `llm_provider=local_ollama`
- stop writing `ollama_base_url` / `ollama_model`
- seed `openrouter_base_url` and leave `openrouter_api_key` / `openrouter_model` empty unless already configured

In `scripts/preflight_local.py`:
- use the same config-first/env-second lookup for `openrouter_api_key` and `openrouter_model`
- use config-first/default-second lookup for `openrouter_base_url`
- fail if key/model are missing
- perform a lightweight OpenRouter reachability check with `GET {base}/models`
- remove Ollama-specific messaging

- [ ] **Step 4: Re-run the preflight tests**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest tests.test_preflight_local -v`

Expected: PASS.

- [ ] **Step 5: Smoke-check the setup script**

Run:

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
backup="./config.json.plan-backup"
cp config.json "$backup"
trap 'mv "$backup" config.json' EXIT
python - <<'PY'
import json
with open('config.json', 'r', encoding='utf-8') as handle:
    cfg = json.load(handle)
cfg['openrouter_api_key'] = 'preserve-key'
cfg['openrouter_model'] = 'preserve-model'
with open('config.json', 'w', encoding='utf-8') as handle:
    json.dump(cfg, handle, indent=2)
    handle.write('\n')
PY
bash scripts/setup_local.sh
python - <<'PY'
import json
with open('config.json', 'r', encoding='utf-8') as handle:
    cfg = json.load(handle)
assert cfg.get('openrouter_base_url') == 'https://openrouter.ai/api/v1'
assert cfg.get('openrouter_api_key') == 'preserve-key'
assert cfg.get('openrouter_model') == 'preserve-model'
assert cfg.get('llm_provider') != 'local_ollama'
assert 'ollama_model' not in cfg or cfg.get('ollama_model') in ('', None)
assert 'ollama_base_url' not in cfg or cfg.get('ollama_base_url') in ('', None)
PY
mv "$backup" config.json
trap - EXIT
```

Expected: setup keeps/creates `openrouter_base_url`, preserves-empty OpenRouter key/model fields, does not re-seed `llm_provider=local_ollama`, does not regenerate non-empty Ollama keys, and restores the original config afterward.

- [ ] **Step 6: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add scripts/setup_local.sh scripts/preflight_local.py tests/test_preflight_local.py
git commit -m "feat: migrate setup and preflight to openrouter"
```

### Task 6: Remove stale Ollama docs and refresh user-facing setup

**Files:**
- Modify: `README.md`
- Modify: `docs/Configuration.md`
- Modify: `docs/AffiliateMarketing.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the docs after code paths are green**

- `README.md`: replace Ollama install/pull instructions and run examples with OpenRouter key/model setup.
- `docs/Configuration.md`: replace Ollama config keys with `openrouter_api_key`, `openrouter_base_url`, and `openrouter_model`, plus fallback/default behavior.
- `docs/AffiliateMarketing.md`: replace Ollama-only architecture statements with OpenRouter-backed text-generation wording.
- `CLAUDE.md`: remove Ollama-only setup and architecture claims.
- After editing docs, run `rg -n "Ollama|ollama" README.md docs/Configuration.md docs/AffiliateMarketing.md CLAUDE.md` and confirm any remaining matches are intentional historical references, not active setup guidance.

- [ ] **Step 2: Run the full test suite**

Run: `cd /Users/cris/.openclaw/workspace/MoneyPrinterV2 && source venv/bin/activate && python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 3: Smoke-check the CLI startup**

Run:

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
backup="./config.json.plan-backup"
cp config.json "$backup"
trap 'mv "$backup" config.json; rm -f Songs/openrouter-smoke.mp3 ./.mp/openrouter-smoke.log' EXIT
python - <<'PY'
import json
with open('config.json', 'r', encoding='utf-8') as handle:
    cfg = json.load(handle)
cfg['openrouter_api_key'] = 'smoke-test-key'
cfg['openrouter_model'] = 'openai/gpt-4.1-mini'
with open('config.json', 'w', encoding='utf-8') as handle:
    json.dump(cfg, handle, indent=2)
    handle.write('\n')
PY
mkdir -p Songs && : > Songs/openrouter-smoke.mp3
mkdir -p .mp
printf '5\n' | python src/main.py > ./.mp/openrouter-smoke.log 2>&1 || true
grep -q "Using configured OpenRouter model: openai/gpt-4.1-mini" ./.mp/openrouter-smoke.log
! grep -q "Could not connect to Ollama" ./.mp/openrouter-smoke.log
mv "$backup" config.json
rm -f Songs/openrouter-smoke.mp3
trap - EXIT
```

Expected:
- log contains `Using configured OpenRouter model: openai/gpt-4.1-mini`
- log does not contain `Could not connect to Ollama`
- app gets past startup and into the normal menu path

- [ ] **Step 4: Commit**

```bash
cd /Users/cris/.openclaw/workspace/MoneyPrinterV2
git add README.md docs/Configuration.md docs/AffiliateMarketing.md CLAUDE.md
git commit -m "docs: replace ollama setup guidance with openrouter"
```
