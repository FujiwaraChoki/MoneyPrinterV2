import json
import pytest
from unittest.mock import patch, MagicMock

# Pre-patch the modules before importing YouTube
import sys

# Mock the problematic imports
sys.modules["moviepy.config"] = MagicMock()

from classes.YouTube import YouTube


@pytest.fixture
def youtube_instance(tmp_path, monkeypatch):
    """Create a YouTube instance with mocked dependencies."""
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    video_path = mp_dir / "test_video.mp4"
    video_path.write_bytes(b"fake video content")

    cache_data = {
        "accounts": [
            {
                "id": "test-uuid",
                "nickname": "test",
                "niche": "tech",
                "language": "English",
                "videos": [],
            }
        ]
    }
    cache_file = mp_dir / "youtube.json"
    cache_file.write_text(json.dumps(cache_data))

    # Mock get_youtube_cache_path to return our test cache path
    monkeypatch.setattr("cache.get_youtube_cache_path", lambda: str(cache_file))

    yt = YouTube(
        account_uuid="test-uuid",
        account_nickname="test",
        niche="tech",
        language="English",
    )
    yt.video_path = str(video_path)
    yt.metadata = {"title": "Test Video", "description": "Test description"}
    yt._niche = "tech"
    yt._cache_file = str(cache_file)  # Store for tests
    return yt


def test_upload_video_calls_api_with_correct_params(youtube_instance):
    """upload_video should call videos().insert() with correct metadata."""
    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_service.videos.return_value.insert.return_value = mock_insert
    mock_insert.next_chunk.return_value = (
        None,
        {"id": "abc123"},
    )

    # Mock the instance method
    youtube_instance.add_video = MagicMock()

    with (
        patch("classes.YouTube.load_credentials", return_value=mock_creds),
        patch("classes.YouTube.build_youtube_service", return_value=mock_service),
        patch("config.get_upload_visibility", return_value="unlisted"),
        patch("classes.YouTube.finalize_video_analytics"),
        patch("cost_tracker._read_analytics", return_value={"pending_costs": []}),
        patch("cost_tracker._write_analytics"),
    ):
        result = youtube_instance.upload_video()

        assert result is True
        mock_service.videos.return_value.insert.assert_called_once()
        call_kwargs = mock_service.videos.return_value.insert.call_args
        body = call_kwargs[1]["body"]
        assert body["snippet"]["title"] == "Test Video"
        assert body["snippet"]["description"] == "Test description"
        assert body["status"]["privacyStatus"] == "unlisted"


def test_upload_video_returns_false_on_auth_error(youtube_instance):
    """upload_video should return False when authentication fails."""
    with patch(
        "classes.YouTube.load_credentials", side_effect=FileNotFoundError("no token")
    ):
        result = youtube_instance.upload_video()
        assert result is False


def test_upload_video_saves_video_to_cache(youtube_instance):
    """upload_video should add the video to the cache after successful upload."""
    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_service.videos.return_value.insert.return_value = mock_insert
    mock_insert.next_chunk.return_value = (
        None,
        {"id": "xyz789"},
    )

    # Mock the instance method
    youtube_instance.add_video = MagicMock()

    with (
        patch("classes.YouTube.load_credentials", return_value=mock_creds),
        patch("classes.YouTube.build_youtube_service", return_value=mock_service),
        patch("config.get_upload_visibility", return_value="unlisted"),
        patch("classes.YouTube.finalize_video_analytics"),
        patch("cost_tracker._read_analytics", return_value={"pending_costs": []}),
        patch("cost_tracker._write_analytics"),
    ):
        result = youtube_instance.upload_video()

        assert result is True
        # Verify add_video was called with correct data
        youtube_instance.add_video.assert_called_once()
        call_args = youtube_instance.add_video.call_args
        video_data = call_args[0][0]
        assert video_data["title"] == "Test Video"
        assert video_data["description"] == "Test description"
        assert "xyz789" in video_data["url"]
