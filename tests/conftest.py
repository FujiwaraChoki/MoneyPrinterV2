import json
import pytest


@pytest.fixture
def tmp_analytics_path(tmp_path):
    """Provides a temporary analytics.json path for testing."""
    path = tmp_path / "analytics.json"
    path.write_text(json.dumps({"videos": [], "pending_costs": []}))
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
    path.write_text(json.dumps({"videos": [sample_video_entry], "pending_costs": []}))
    return str(path)
