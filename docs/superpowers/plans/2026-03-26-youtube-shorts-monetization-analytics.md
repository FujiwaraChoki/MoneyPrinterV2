# YouTube Shorts Monetization Analytics — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cost tracking and YouTube Data API metrics collection to MoneyPrinterV2 so users can compare monetization effectiveness across niches.

**Architecture:** Extend the existing JSON-based cache with a new `analytics.json` file. Add three new modules (`cost_tracker.py`, `analytics.py`, `report.py`) and hook cost recording into the existing `YouTube.generate_image()` pipeline. Metrics are fetched via YouTube Data API v3 and displayed through CLI + CSV export.

**Tech Stack:** Python 3.12, google-api-python-client, google-auth-oauthlib, PrettyTable, existing project patterns

**Spec:** `docs/superpowers/specs/2026-03-26-youtube-shorts-monetization-analytics-design.md`

---

## File Map

### New Files

| File | Responsibility |
|------|---------------|
| `src/cost_tracker.py` | Record and query per-video Gemini API costs in `.mp/analytics.json` |
| `src/analytics.py` | YouTube Data API v3 OAuth + metrics fetch (views, likes, comments) |
| `src/report.py` | CLI summary table (PrettyTable) + CSV export to `exports/` |
| `tests/test_cost_tracker.py` | Unit tests for cost_tracker |
| `tests/test_report.py` | Unit tests for report |
| `tests/conftest.py` | Shared pytest fixtures (tmp analytics JSON, etc.) |

### Modified Files

| File | Change |
|------|--------|
| `config.example.json` | Add `google_api_credentials_path`, `gemini_cost_per_call` |
| `src/config.py` | Add `get_google_api_credentials_path()`, `get_gemini_cost_per_call()` |
| `src/constants.py` | Add `"Analytics"` to `OPTIONS` list |
| `src/classes/YouTube.py` | Hook cost_tracker in `generate_image()` and `upload_video()` |
| `src/main.py` | Add Analytics menu (option 5), shift Quit to option 6 |
| `requirements.txt` | Add `google-api-python-client`, `google-auth-oauthlib`, `pytest` |

---

## Task 1: Repository & Test Infrastructure Setup

**Files:**
- Modify: `requirements.txt`
- Create: `tests/conftest.py`
- Create: `pytest.ini`

- [ ] **Step 1: Fork the repository on GitHub**

The user needs to fork MoneyPrinterV2 on GitHub. Then update the local remote:

```bash
# On GitHub: Fork FujiwaraChoki/MoneyPrinterV2 to your account
# Then update the local remote:
git remote rename origin upstream
git remote add origin git@github.com:<YOUR_USERNAME>/MoneyPrinterV2.git
git push -u origin main
```

This step requires the user's GitHub username. Ask before proceeding.

- [ ] **Step 2: Add dependencies to requirements.txt**

Append these lines to `requirements.txt`:

```
google-api-python-client
google-auth-oauthlib
pytest
```

- [ ] **Step 3: Install dependencies**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2
source venv/bin/activate && pip install -r requirements.txt
```

If no venv exists yet:
```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

- [ ] **Step 4: Create pytest.ini**

Create `pytest.ini` at project root:

```ini
[pytest]
testpaths = tests
pythonpath = src
```

`pythonpath = src` ensures tests can import modules the same way the app does (bare `from config import *`).

- [ ] **Step 5: Create tests/conftest.py**

```python
import os
import json
import pytest


@pytest.fixture
def tmp_analytics_path(tmp_path):
    """Provides a temporary analytics.json path for testing."""
    path = tmp_path / "analytics.json"
    path.write_text(json.dumps({"videos": []}))
    return str(path)


@pytest.fixture
def sample_video_entry():
    """A complete video entry for testing."""
    return {
        "video_id": "test123",
        "title": "Test Video",
        "niche": "cooking",
        "upload_date": "2026-03-26 10:00:00",
        "cost": {
            "gemini_api_calls": 5,
            "gemini_model": "gemini-3.1-flash-image-preview",
        },
        "metrics_history": [],
    }


@pytest.fixture
def analytics_with_data(tmp_path, sample_video_entry):
    """Analytics JSON pre-populated with one video."""
    path = tmp_path / "analytics.json"
    path.write_text(json.dumps({"videos": [sample_video_entry]}))
    return str(path)
```

- [ ] **Step 6: Verify test infrastructure works**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/ -v --co
```

Expected: `no tests ran` (collected 0 items). No import errors.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pytest.ini tests/conftest.py
git commit -m "chore: add test infrastructure and analytics dependencies"
```

---

## Task 2: Cost Tracker Module (TDD)

**Files:**
- Create: `src/cost_tracker.py`
- Create: `tests/test_cost_tracker.py`

- [ ] **Step 1: Write failing tests for cost_tracker**

Create `tests/test_cost_tracker.py`:

```python
import json
import pytest
from cost_tracker import record_image_cost, get_video_cost, get_all_costs


class TestRecordImageCost:
    def test_records_single_call(self, tmp_analytics_path):
        record_image_cost(
            video_id="vid1",
            model="gemini-3.1-flash-image-preview",
            analytics_path=tmp_analytics_path,
        )
        data = json.loads(open(tmp_analytics_path).read())
        costs = data["pending_costs"]
        assert len(costs) == 1
        assert costs[0]["video_id"] == "vid1"
        assert costs[0]["gemini_api_calls"] == 1

    def test_accumulates_multiple_calls(self, tmp_analytics_path):
        for _ in range(3):
            record_image_cost(
                video_id="vid1",
                model="gemini-3.1-flash-image-preview",
                analytics_path=tmp_analytics_path,
            )
        data = json.loads(open(tmp_analytics_path).read())
        # Should accumulate into one entry
        pending = [c for c in data["pending_costs"] if c["video_id"] == "vid1"]
        assert len(pending) == 1
        assert pending[0]["gemini_api_calls"] == 3


class TestGetVideoCost:
    def test_returns_cost_for_known_video(self, analytics_with_data):
        cost = get_video_cost("test123", analytics_path=analytics_with_data)
        assert cost["gemini_api_calls"] == 5

    def test_returns_none_for_unknown_video(self, analytics_with_data):
        cost = get_video_cost("unknown", analytics_path=analytics_with_data)
        assert cost is None


class TestGetAllCosts:
    def test_returns_all_video_costs(self, analytics_with_data):
        costs = get_all_costs(analytics_path=analytics_with_data)
        assert len(costs) == 1
        assert costs[0]["video_id"] == "test123"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/test_cost_tracker.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'cost_tracker'`

- [ ] **Step 3: Implement cost_tracker.py**

Create `src/cost_tracker.py`:

```python
import os
import json

from config import ROOT_DIR


def _get_default_analytics_path() -> str:
    return os.path.join(ROOT_DIR, ".mp", "analytics.json")


def _read_analytics(analytics_path: str | None = None) -> dict:
    path = analytics_path or _get_default_analytics_path()
    if not os.path.exists(path):
        return {"videos": [], "pending_costs": []}
    with open(path, "r") as f:
        data = json.load(f)
    if "pending_costs" not in data:
        data["pending_costs"] = []
    return data


def _write_analytics(data: dict, analytics_path: str | None = None) -> None:
    path = analytics_path or _get_default_analytics_path()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record_image_cost(
    video_id: str,
    model: str,
    analytics_path: str | None = None,
) -> None:
    """Record one Gemini API image generation call for a video.

    Called once per generate_image() invocation. Accumulates calls
    in pending_costs until the video is finalized via finalize_video().
    """
    data = _read_analytics(analytics_path)
    pending = data["pending_costs"]

    existing = next((c for c in pending if c["video_id"] == video_id), None)
    if existing:
        existing["gemini_api_calls"] += 1
    else:
        pending.append({
            "video_id": video_id,
            "gemini_api_calls": 1,
            "gemini_model": model,
        })

    _write_analytics(data, analytics_path)


def finalize_video(
    video_id: str,
    title: str,
    niche: str,
    upload_date: str,
    analytics_path: str | None = None,
) -> None:
    """Move pending cost data into a completed video entry."""
    data = _read_analytics(analytics_path)

    cost_entry = next(
        (c for c in data["pending_costs"] if c["video_id"] == video_id),
        None,
    )
    cost = {
        "gemini_api_calls": cost_entry["gemini_api_calls"] if cost_entry else 0,
        "gemini_model": cost_entry["gemini_model"] if cost_entry else "",
    }

    data["videos"].append({
        "video_id": video_id,
        "title": title,
        "niche": niche,
        "upload_date": upload_date,
        "cost": cost,
        "metrics_history": [],
    })

    if cost_entry:
        data["pending_costs"].remove(cost_entry)

    _write_analytics(data, analytics_path)


def get_video_cost(video_id: str, analytics_path: str | None = None) -> dict | None:
    """Get cost data for a specific video."""
    data = _read_analytics(analytics_path)
    for video in data["videos"]:
        if video["video_id"] == video_id:
            return video["cost"]
    return None


def get_all_costs(analytics_path: str | None = None) -> list[dict]:
    """Get cost summary for all videos: [{video_id, niche, gemini_api_calls, ...}]."""
    data = _read_analytics(analytics_path)
    return [
        {
            "video_id": v["video_id"],
            "title": v["title"],
            "niche": v["niche"],
            "upload_date": v["upload_date"],
            "gemini_api_calls": v["cost"]["gemini_api_calls"],
            "gemini_model": v["cost"]["gemini_model"],
        }
        for v in data["videos"]
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/test_cost_tracker.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cost_tracker.py tests/test_cost_tracker.py
git commit -m "feat: add cost_tracker module with TDD tests"
```

---

## Task 3: Config Additions

**Files:**
- Modify: `src/config.py`
- Modify: `config.example.json`

- [ ] **Step 1: Add fields to config.example.json**

Add before the closing `}` (after `"script_sentence_length": 4`):

```json
  "google_api_credentials_path": "",
  "gemini_cost_per_call": 0.005
```

The full line to modify — change:
```json
  "script_sentence_length": 4
}
```
to:
```json
  "script_sentence_length": 4,
  "google_api_credentials_path": "",
  "gemini_cost_per_call": 0.005
}
```

- [ ] **Step 2: Add getter functions to config.py**

Append to end of `src/config.py` (after `get_script_sentence_length()`):

```python
def get_google_api_credentials_path() -> str:
    """
    Gets the path to the Google API OAuth credentials JSON file.

    Returns:
        path (str): Path to credentials.json
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("google_api_credentials_path", "")

def get_gemini_cost_per_call() -> float:
    """
    Gets the cost per Gemini API image generation call.

    Returns:
        cost (float): Cost in USD per call
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("gemini_cost_per_call", 0.005)
```

- [ ] **Step 3: Commit**

```bash
git add src/config.py config.example.json
git commit -m "feat: add Google API and cost config getters"
```

---

## Task 4: YouTube.py Cost Tracking Integration

**Files:**
- Modify: `src/classes/YouTube.py`

- [ ] **Step 1: Add import at top of YouTube.py**

After the existing `from datetime import datetime` import (line 29), add:

```python
from cost_tracker import record_image_cost, finalize_video
```

- [ ] **Step 2: Add a pending video ID to __init__**

The video doesn't have a YouTube video_id until after upload. We need a temporary local ID to track costs during generation. In `__init__`, after `self.images = []` (around line 67), add:

```python
        self._pending_video_id = str(uuid4())
```

- [ ] **Step 3: Hook cost recording into generate_image()**

In `generate_image()` (line 380-390), change:

```python
    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt using Nano Banana 2.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        return self.generate_image_nanobanana2(prompt)
```

to:

```python
    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt using Nano Banana 2.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        result = self.generate_image_nanobanana2(prompt)
        if result is not None:
            record_image_cost(
                video_id=self._pending_video_id,
                model=get_nanobanana2_model(),
            )
        return result
```

- [ ] **Step 4: Finalize video after successful upload**

In `upload_video()`, after the `self.add_video(...)` block (line 838-844), add:

```python
            finalize_video(
                video_id=video_id,
                title=self.metadata["title"],
                niche=self.niche,
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
```

Also, we need to update the pending_video_id to the real YouTube video_id in the cost tracker. Add this right before the `finalize_video()` call:

```python
            # Update pending cost entry with real YouTube video_id
            from cost_tracker import _read_analytics, _write_analytics
            analytics_data = _read_analytics()
            for entry in analytics_data.get("pending_costs", []):
                if entry["video_id"] == self._pending_video_id:
                    entry["video_id"] = video_id
                    break
            _write_analytics(analytics_data)
```

- [ ] **Step 5: Verify no import errors**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); from classes.YouTube import YouTube; print('OK')"
```

Expected: `OK` (no import errors).

- [ ] **Step 6: Commit**

```bash
git add src/classes/YouTube.py
git commit -m "feat: integrate cost tracking into YouTube video pipeline"
```

---

## Task 5: Analytics Module — YouTube Data API Client

**Files:**
- Create: `src/analytics.py`

- [ ] **Step 1: Create analytics.py**

Create `src/analytics.py`:

```python
import os
import json

from config import ROOT_DIR, get_google_api_credentials_path
from cost_tracker import _read_analytics, _write_analytics
from status import error, info, success, warning


SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_PATH = os.path.join(ROOT_DIR, ".mp", "google_token.json")


def _get_youtube_service():
    """Build and return an authenticated YouTube Data API v3 service.

    Uses OAuth 2.0 installed-app flow. On first run, opens a local
    server for the OAuth consent flow (headless-friendly: prints URL).
    Subsequent calls use the cached token.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = get_google_api_credentials_path()
            if not credentials_path or not os.path.exists(credentials_path):
                error("Google API credentials not configured. Set google_api_credentials_path in config.json.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Use console-based flow for headless server
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def fetch_metrics_for_video(video_id: str) -> dict | None:
    """Fetch current metrics for a single video from YouTube Data API.

    Returns:
        dict with keys: views, likes, comments, fetched_at
        None if the API call fails.
    """
    from datetime import datetime

    service = _get_youtube_service()
    if service is None:
        return None

    try:
        response = service.videos().list(
            part="statistics",
            id=video_id,
        ).execute()

        items = response.get("items", [])
        if not items:
            warning(f"No video found for ID: {video_id}")
            return None

        stats = items[0]["statistics"]
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        error(f"Failed to fetch metrics for {video_id}: {e}")
        return None


def fetch_all_metrics(analytics_path: str | None = None) -> int:
    """Fetch metrics for all tracked videos and append to metrics_history.

    Returns:
        count of successfully updated videos.
    """
    data = _read_analytics(analytics_path)
    updated = 0

    for video in data["videos"]:
        video_id = video["video_id"]
        info(f"Fetching metrics for: {video.get('title', video_id)}")
        metrics = fetch_metrics_for_video(video_id)

        if metrics is not None:
            video["metrics_history"].append(metrics)
            updated += 1
            success(f"  views={metrics['views']}, likes={metrics['likes']}, comments={metrics['comments']}")

    _write_analytics(data, analytics_path)
    return updated
```

- [ ] **Step 2: Verify no import errors**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); import analytics; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/analytics.py
git commit -m "feat: add YouTube Data API v3 metrics collection module"
```

---

## Task 6: Report Module (TDD)

**Files:**
- Create: `src/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_report.py`:

```python
import csv
import json
import os
import pytest
from report import generate_niche_summary, export_csv


@pytest.fixture
def multi_video_analytics(tmp_path):
    """Analytics with multiple niches for report testing."""
    path = tmp_path / "analytics.json"
    data = {
        "videos": [
            {
                "video_id": "v1",
                "title": "Pasta Recipe",
                "niche": "cooking",
                "upload_date": "2026-03-20 10:00:00",
                "cost": {"gemini_api_calls": 5, "gemini_model": "gemini-3.1-flash-image-preview"},
                "metrics_history": [
                    {"views": 1000, "likes": 50, "comments": 5, "fetched_at": "2026-03-25 10:00:00"},
                ],
            },
            {
                "video_id": "v2",
                "title": "Salad Tips",
                "niche": "cooking",
                "upload_date": "2026-03-21 10:00:00",
                "cost": {"gemini_api_calls": 4, "gemini_model": "gemini-3.1-flash-image-preview"},
                "metrics_history": [
                    {"views": 2000, "likes": 80, "comments": 10, "fetched_at": "2026-03-25 10:00:00"},
                ],
            },
            {
                "video_id": "v3",
                "title": "HIIT Workout",
                "niche": "fitness",
                "upload_date": "2026-03-22 10:00:00",
                "cost": {"gemini_api_calls": 6, "gemini_model": "gemini-3.1-flash-image-preview"},
                "metrics_history": [
                    {"views": 500, "likes": 20, "comments": 2, "fetched_at": "2026-03-25 10:00:00"},
                ],
            },
        ],
        "pending_costs": [],
    }
    path.write_text(json.dumps(data))
    return str(path)


class TestNicheSummary:
    def test_aggregates_by_niche(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.005,
            analytics_path=multi_video_analytics,
        )
        assert len(summary) == 2

        cooking = next(s for s in summary if s["niche"] == "cooking")
        assert cooking["video_count"] == 2
        assert cooking["total_views"] == 3000
        assert cooking["total_likes"] == 130

        fitness = next(s for s in summary if s["niche"] == "fitness")
        assert fitness["video_count"] == 1
        assert fitness["total_views"] == 500

    def test_calculates_cost(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.01,
            analytics_path=multi_video_analytics,
        )
        cooking = next(s for s in summary if s["niche"] == "cooking")
        # 5 + 4 = 9 calls * $0.01 = $0.09
        assert cooking["total_cost"] == pytest.approx(0.09)

    def test_calculates_views_per_cost(self, multi_video_analytics):
        summary = generate_niche_summary(
            cost_per_call=0.01,
            analytics_path=multi_video_analytics,
        )
        cooking = next(s for s in summary if s["niche"] == "cooking")
        # 3000 views / $0.09 cost
        assert cooking["views_per_cost"] == pytest.approx(3000 / 0.09)


class TestCsvExport:
    def test_creates_csv_file(self, multi_video_analytics, tmp_path):
        out = str(tmp_path / "export.csv")
        export_csv(output_path=out, analytics_path=multi_video_analytics)
        assert os.path.exists(out)

    def test_csv_has_correct_rows(self, multi_video_analytics, tmp_path):
        out = str(tmp_path / "export.csv")
        export_csv(output_path=out, analytics_path=multi_video_analytics)
        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["video_id"] == "v1"
        assert rows[0]["niche"] == "cooking"
        assert rows[0]["views"] == "1000"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/test_report.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'report'`

- [ ] **Step 3: Implement report.py**

Create `src/report.py`:

```python
import csv
import os
from datetime import datetime

from config import ROOT_DIR, get_gemini_cost_per_call
from cost_tracker import _read_analytics


def generate_niche_summary(
    cost_per_call: float | None = None,
    analytics_path: str | None = None,
) -> list[dict]:
    """Aggregate video data by niche.

    Returns a list of dicts, each with:
        niche, video_count, total_views, total_likes, total_comments,
        total_api_calls, total_cost, views_per_cost
    """
    if cost_per_call is None:
        cost_per_call = get_gemini_cost_per_call()

    data = _read_analytics(analytics_path)
    niches: dict[str, dict] = {}

    for video in data["videos"]:
        niche = video["niche"]
        if niche not in niches:
            niches[niche] = {
                "niche": niche,
                "video_count": 0,
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_api_calls": 0,
            }

        entry = niches[niche]
        entry["video_count"] += 1
        entry["total_api_calls"] += video["cost"]["gemini_api_calls"]

        # Use latest metrics snapshot if available
        if video["metrics_history"]:
            latest = video["metrics_history"][-1]
            entry["total_views"] += latest["views"]
            entry["total_likes"] += latest["likes"]
            entry["total_comments"] += latest["comments"]

    result = []
    for entry in niches.values():
        total_cost = entry["total_api_calls"] * cost_per_call
        views_per_cost = entry["total_views"] / total_cost if total_cost > 0 else 0
        result.append({
            **entry,
            "total_cost": total_cost,
            "views_per_cost": views_per_cost,
        })

    return sorted(result, key=lambda x: x["views_per_cost"], reverse=True)


def print_niche_summary(analytics_path: str | None = None) -> None:
    """Print a formatted niche summary table to the terminal."""
    from prettytable import PrettyTable

    summary = generate_niche_summary(analytics_path=analytics_path)

    if not summary:
        print("No analytics data found.")
        return

    table = PrettyTable()
    table.field_names = ["Niche", "Videos", "Views", "Likes", "Comments", "Cost", "Views/Cost"]

    for row in summary:
        table.add_row([
            row["niche"],
            row["video_count"],
            f"{row['total_views']:,}",
            f"{row['total_likes']:,}",
            f"{row['total_comments']:,}",
            f"${row['total_cost']:.3f}",
            f"{row['views_per_cost']:,.0f}",
        ])

    print(table)


def export_csv(
    output_path: str | None = None,
    analytics_path: str | None = None,
) -> str:
    """Export per-video analytics data to CSV.

    Returns:
        path to the created CSV file.
    """
    if output_path is None:
        exports_dir = os.path.join(ROOT_DIR, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(exports_dir, f"analytics_{date_str}.csv")

    data = _read_analytics(analytics_path)

    fieldnames = [
        "video_id", "title", "niche", "upload_date",
        "gemini_api_calls", "views", "likes", "comments", "fetched_at",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for video in data["videos"]:
            latest_metrics = video["metrics_history"][-1] if video["metrics_history"] else {}
            writer.writerow({
                "video_id": video["video_id"],
                "title": video["title"],
                "niche": video["niche"],
                "upload_date": video["upload_date"],
                "gemini_api_calls": video["cost"]["gemini_api_calls"],
                "views": latest_metrics.get("views", ""),
                "likes": latest_metrics.get("likes", ""),
                "comments": latest_metrics.get("comments", ""),
                "fetched_at": latest_metrics.get("fetched_at", ""),
            })

    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/test_report.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report.py tests/test_report.py
git commit -m "feat: add report module with niche summary and CSV export"
```

---

## Task 7: Main Menu Integration

**Files:**
- Modify: `src/constants.py`
- Modify: `src/main.py`

- [ ] **Step 1: Add Analytics to OPTIONS in constants.py**

Change `OPTIONS` (line 8-14):

```python
OPTIONS = [
    "YouTube Shorts Automation",
    "Twitter Bot",
    "Affiliate Marketing",
    "Outreach",
    "Quit"
]
```

to:

```python
OPTIONS = [
    "YouTube Shorts Automation",
    "Twitter Bot",
    "Affiliate Marketing",
    "Outreach",
    "Analytics",
    "Quit"
]
```

Also add analytics sub-options:

```python
ANALYTICS_OPTIONS = [
    "Niche Summary",
    "Fetch Latest Metrics",
    "Export CSV",
    "Quit"
]
```

- [ ] **Step 2: Add imports to main.py**

After the existing imports (line 18), add:

```python
from analytics import fetch_all_metrics
from report import print_niche_summary, export_csv
```

- [ ] **Step 3: Add Analytics menu handler to main.py**

The current option 5 (`user_input == 5`) is Quit (line 420-423). We need to:
1. Insert the Analytics block as `elif user_input == 5`
2. Change Quit to `elif user_input == 6`

Before the current `elif user_input == 5:` (line 420), insert:

```python
    elif user_input == 5:
        info("Starting Analytics...")

        while True:
            info("\n============ OPTIONS ============", False)

            for idx, option in enumerate(ANALYTICS_OPTIONS):
                print(colored(f" {idx + 1}. {option}", "cyan"))

            info("=================================\n", False)

            user_input = int(question("Select an option: "))

            if user_input == 1:
                print_niche_summary()
            elif user_input == 2:
                count = fetch_all_metrics()
                success(f"Updated metrics for {count} videos.")
            elif user_input == 3:
                path = export_csv()
                success(f"Exported to: {path}")
            elif user_input == 4:
                break
```

Then change the old option 5 (Quit) to option 6:

```python
    elif user_input == 6:
```

- [ ] **Step 4: Also import ANALYTICS_OPTIONS in main.py**

The existing `from constants import *` (line 10) already covers this since we added `ANALYTICS_OPTIONS` to constants.py.

- [ ] **Step 5: Verify syntax**

Run:
```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -c "import sys; sys.path.insert(0, 'src'); import main; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add src/constants.py src/main.py
git commit -m "feat: add Analytics menu to main CLI with summary, fetch, and export"
```

---

## Task 8: Integration Verification

- [ ] **Step 1: Run all tests**

```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -m pytest tests/ -v
```

Expected: All tests pass (cost_tracker + report).

- [ ] **Step 2: Verify CLI loads without errors**

```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && timeout 3 python -c "
import sys
sys.path.insert(0, 'src')
from constants import OPTIONS, ANALYTICS_OPTIONS
from cost_tracker import record_image_cost, finalize_video, get_all_costs
from analytics import fetch_all_metrics
from report import generate_niche_summary, print_niche_summary, export_csv

print('OPTIONS:', OPTIONS)
print('ANALYTICS_OPTIONS:', ANALYTICS_OPTIONS)
print('All modules import OK')
" 2>&1 || true
```

Expected: Prints options lists and "All modules import OK".

- [ ] **Step 3: Test cost tracking end-to-end with mock data**

```bash
cd /home/server160/repos/MoneyPrinterV2 && source venv/bin/activate && python -c "
import sys, json, os, tempfile
sys.path.insert(0, 'src')

from cost_tracker import record_image_cost, finalize_video, get_all_costs
from report import generate_niche_summary, export_csv

# Use temp file
tmp = tempfile.mktemp(suffix='.json')
with open(tmp, 'w') as f:
    json.dump({'videos': [], 'pending_costs': []}, f)

# Simulate video generation
record_image_cost('pending1', 'gemini-3.1-flash-image-preview', tmp)
record_image_cost('pending1', 'gemini-3.1-flash-image-preview', tmp)
record_image_cost('pending1', 'gemini-3.1-flash-image-preview', tmp)

# Simulate upload complete
finalize_video('pending1', 'Test Video', 'cooking', '2026-03-26 10:00:00', tmp)

# Add metrics manually (simulating API fetch)
data = json.loads(open(tmp).read())
data['videos'][0]['metrics_history'].append({
    'views': 1500, 'likes': 60, 'comments': 5, 'fetched_at': '2026-03-27 10:00:00'
})
with open(tmp, 'w') as f:
    json.dump(data, f, indent=2)

# Generate report
summary = generate_niche_summary(cost_per_call=0.005, analytics_path=tmp)
print('Niche summary:', summary)

# Export CSV
csv_path = tempfile.mktemp(suffix='.csv')
export_csv(output_path=csv_path, analytics_path=tmp)
print('CSV exported to:', csv_path)
print('CSV content:')
print(open(csv_path).read())

# Cleanup
os.unlink(tmp)
os.unlink(csv_path)
print('Integration test PASSED')
"
```

Expected: Prints summary with cooking niche, CSV content with the video data, and "Integration test PASSED".

- [ ] **Step 4: Commit and final status**

```bash
git status
```

Verify working tree is clean. All changes committed.

---

## Task 9: Housekeeping

- [ ] **Step 1: Add exports/ to .gitignore**

Create or append to `.gitignore`:

```
exports/
.mp/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore exports and .mp data directories"
```

---

## Remaining Setup (User Action Required)

After the code is implemented, the user needs to:

1. **Fork the repo on GitHub** and update remotes (Task 1, Step 1)
2. **Set up config.json** — copy from config.example.json and fill in Ollama model, Gemini API key, Firefox profile, ImageMagick path
3. **Create Google Cloud OAuth credentials** for YouTube Data API v3:
   - Go to Google Cloud Console → APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Desktop app type)
   - Download `credentials.json` and set path in config.json
   - Enable YouTube Data API v3 in the project
4. **Run the first OAuth flow** — on first `Fetch Metrics`, it will print a URL to authorize
5. **Generate and upload test videos** across 3-5 niches
6. **Fetch metrics** periodically and review the niche summary
